from pathlib import Path

import pandas as pd
import numpy as np

from app_support import log_event


class OptionChain:

    def __init__(self, csv_file):
        self.csv_file = Path(csv_file)
        self.df = None

    # ----------------------------------------------------
    # Load CSV
    # ----------------------------------------------------
    def load(self):

        self.df = pd.read_csv(self.csv_file)

        log_event("option_chain_loaded", filename=str(self.csv_file.name), rows=len(self.df))

        return self.df

    # ----------------------------------------------------
    # Clean Data
    # ----------------------------------------------------
    def clean(self):

        if self.df is None:
            raise Exception("Load CSV first.")

        # Replace invalid values
        self.df = self.df.mask(self.df.isin(["--", "-", "", " ", "NA", "N/A"]), np.nan)

        # Remove fully empty rows
        self.df.dropna(how="all", inplace=True)

        self.df.reset_index(drop=True, inplace=True)

        return self.df

    # ----------------------------------------------------
    # Convert Numeric Columns
    # ----------------------------------------------------
    def convert_numeric(self):

        if self.df is None:
            raise Exception("Load CSV first.")

        object_columns = self.df.select_dtypes(include="object").columns

        for col in object_columns:

            cleaned = (
                self.df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )

            numeric = pd.to_numeric(cleaned, errors="coerce")

            # All quote columns are numeric even if every value is missing.
            if col != "Instrument":
                self.df[col] = numeric

        return self.df
    
    #----------------------------------------------------
    # Rename Columns
    #----------------------------------------------------
    def rename_columns(self):

        COLUMN_MAPPING = {

            "Strike": "Strike",
            "IV": "IV",
            "Instrument": "Instrument",
            "PCR": "PCR",

            "Call LTP": "CallLTP",
            "Call Time Value": "CallTimeValue",
            "Call Intrinsic Value(Spot)": "CallIntrinsicSpot",
            "Call Intrinsic Value(Fut)": "CallIntrinsicFuture",
            "Call Bid Price": "CallBid",
            "Call Offer Price": "CallAsk",
            "Call OI": "CallOI",
            "Call Change %": "CallOIChangePct",
            "Call OI Change": "CallOIChange",
            "Call Volume": "CallVolume",
            "Call POP %": "CallPOP",
            "Call Delta": "CallDelta",
            "Call Theta": "CallTheta",
            "Call Vega": "CallVega",
            "Call Gamma": "CallGamma",

            "Put LTP": "PutLTP",
            "Put Time Value": "PutTimeValue",
            "Put Intrinsic Value(Spot)": "PutIntrinsicSpot",
            "Put Intrinsic Value(Fut)": "PutIntrinsicFuture",
            "Put Bid Price": "PutBid",
            "Put Offer Price": "PutAsk",
            "Put OI": "PutOI",
            "Put Change %": "PutOIChangePct",
            "Put OI Change": "PutOIChange",
            "Put Volume": "PutVolume",
            "Put POP %": "PutPOP",
            "Put Delta": "PutDelta",
            "Put Theta": "PutTheta",
            "Put Vega": "PutVega",
            "Put Gamma": "PutGamma"
        }

        self.df.rename(columns=COLUMN_MAPPING, inplace=True)

    # ----------------------------------------------------
    # Validate Columns
    # ----------------------------------------------------
    def validate(self):

        REQUIRED_COLUMNS = [

            # Common
            "Strike",
            "IV",
            "PCR",

            # Call
            "CallLTP",
            "CallBid",
            "CallAsk",
            "CallOI",
            "CallOIChange",
            "CallVolume",
            "CallDelta",
            "CallTheta",
            "CallVega",
            "CallGamma",

            # Put
            "PutLTP",
            "PutBid",
            "PutAsk",
            "PutOI",
            "PutOIChange",
            "PutVolume",
            "PutDelta",
            "PutTheta",
            "PutVega",
            "PutGamma"
        ]

        missing = []

        for col in REQUIRED_COLUMNS:

            if col not in self.df.columns:
                missing.append(col)

        if missing:
            raise ValueError("CSV is missing required columns: " + ", ".join(missing))
        if self.df.empty:
            raise ValueError("The uploaded option chain is empty.")
        if not np.isfinite(self.df["Strike"]).all() or (self.df["Strike"] <= 0).any():
            raise ValueError("The option chain contains invalid strikes.")
        if self.df["Strike"].duplicated().any():
            raise ValueError("The option chain contains duplicate strikes.")
        if "Instrument" in self.df and not self.df["Instrument"].astype(str).str.strip().str.upper().eq("NIFTY").all():
            raise ValueError("Only NIFTY option-chain CSVs are supported.")
        for side in ("Call", "Put"):
            essential = ["IV"] + [side + suffix for suffix in ("LTP", "Bid", "Ask", "OI", "Volume", "Delta", "Theta", "Vega")]
            valid = np.isfinite(self.df[essential]).all(axis=1)
            valid &= self.df["IV"].gt(0) & self.df[side + "LTP"].gt(0)
            valid &= self.df[side + "Bid"].gt(0) & self.df[side + "Ask"].ge(self.df[side + "Bid"])
            valid &= self.df[side + "OI"].ge(0) & self.df[side + "Volume"].ge(0)
            delta = self.df[side + "Delta"]
            valid &= delta.between(0, 1) if side == "Call" else delta.between(-1, 0)
            self.df[side + "DataValid"] = valid
        log_event("option_chain_validated", rows=len(self.df),
                  invalid_calls=int((~self.df.CallDataValid).sum()),
                  invalid_puts=int((~self.df.PutDataValid).sum()))

    def snapshot_underlying(self, kind="Spot"):
        """Recover the recorded underlying from ITM intrinsic values, not LTP/model guesses."""
        prices = []
        for side in ("Call", "Put"):
            column = side + "Intrinsic" + ("Spot" if kind == "Spot" else "Future")
            if column not in self.df:
                continue
            rows = self.df.loc[self.df[column].gt(0) & np.isfinite(self.df[column])]
            values = rows["Strike"] + rows[column] if side == "Call" else rows["Strike"] - rows[column]
            prices.extend(values[np.isfinite(values) & values.gt(0)].tolist())
        if not prices:
            return None
        if max(prices) - min(prices) > 0.1:
            raise ValueError(f"CSV intrinsic values imply inconsistent {kind.lower()} prices.")
        return round(float(np.median(prices)), 2)