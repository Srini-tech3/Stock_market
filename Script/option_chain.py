import pandas as pd
import numpy as np


class OptionChain:

    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = None

    # ----------------------------------------------------
    # Load CSV
    # ----------------------------------------------------
    def load(self):

        self.df = pd.read_csv(self.csv_file)

        print(f"\nLoaded {len(self.df)} rows")

        return self.df

    # ----------------------------------------------------
    # Clean Data
    # ----------------------------------------------------
    def clean(self):

        if self.df is None:
            raise Exception("Load CSV first.")

        # Replace invalid values
        self.df.replace(
            ["--", "-", "", " ", "NA", "N/A"],
            np.nan,
            inplace=True
        )

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

            # Convert only if at least one numeric value exists
            if numeric.notna().sum() > 0:
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

            print("\nMissing Columns")

            for c in missing:
                print("   ", c)

            raise Exception("CSV format not supported.")

        print("\nCSV validation successful.")