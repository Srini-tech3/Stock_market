from pathlib import Path
from datetime import date, datetime, timedelta
import math
import re
import sys

import pandas as pd
from openpyxl import load_workbook

from app_support import atomic_workbook


def project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class ConfigManager:
    """Keep Config.xlsx as the existing rulebook; discover uploaded CSV snapshots."""

    NUMERIC_RULES = (
        "SpotPrice", "VIX", "LotSize", "WingWidth", "AvailableCapital", "MinPOP",
        "MinDelta", "MaxDelta", "MinOI", "MinVolume", "MaxBidAskPct",
        "MaxSpreadPoints", "MaxCapitalPerTrade",
    )

    def __init__(self, input_dir=None, output_dir=None, config_file=None):
        self.input_dir = Path(input_dir) if input_dir else project_root() / "Input"
        self.output_dir = Path(output_dir) if output_dir else project_root() / "Output"
        self.config_file = Path(config_file) if config_file else self.input_dir / "Config.xlsx"

    def load_config(self):
        if not self.config_file.exists():
            raise ValueError(f"Configuration workbook not found: {self.config_file}")
        df = pd.read_excel(self.config_file, sheet_name="CONFIG")
        if not {"Parameter", "Value"}.issubset(df.columns):
            raise ValueError("CONFIG sheet must contain Parameter and Value columns.")
        if df["Parameter"].duplicated().any():
            raise ValueError("CONFIG sheet contains duplicate parameters.")
        values = dict(zip(df["Parameter"], df["Value"]))
        for key in self.NUMERIC_RULES:
            try:
                number = float(values[key])
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"Config.xlsx requires a numeric {key}.") from None
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"Config.xlsx has an invalid {key}.")
        for key in ("LotSize", "WingWidth", "AvailableCapital", "MaxCapitalPerTrade"):
            if float(values[key]) <= 0:
                raise ValueError(f"{key} must be greater than zero.")
        for key in ("LotSize", "WingWidth", "MinOI", "MinVolume"):
            if not float(values[key]).is_integer():
                raise ValueError(f"{key} must be a whole number.")
        if not 0 <= float(values["MinDelta"]) <= float(values["MaxDelta"]) <= 1:
            raise ValueError("Delta rules must satisfy 0 <= MinDelta <= MaxDelta <= 1.")
        if not 0 <= float(values["MinPOP"]) <= 100:
            raise ValueError("MinPOP must be between 0 and 100.")
        for key in ("MinimumCredit", "MinimumROR"):
            if key in values and (not math.isfinite(float(values[key])) or float(values[key]) < 0):
                raise ValueError(f"{key} must be a non-negative number.")
        return values

    def _extract_expiry_from_name(self, filename):
        match = re.search(r"_(\d{4}-\d{2}-\d{2})_option_chain", filename, re.IGNORECASE)
        if match:
            try:
                return date.fromisoformat(match.group(1))
            except ValueError:
                pass
        return None

    def snapshot_time(self, csv_file):
        match = re.search(r"_option_chain_(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})", Path(csv_file).name)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d-%H-%M-%S").isoformat()
            except ValueError:
                pass
        return None

    def available_snapshots(self):
        snapshots = []
        for file in self.input_dir.glob("*.csv"):
            expiry = self._extract_expiry_from_name(file.name)
            if expiry is None:
                continue
            snapshots.append({
                "filename": file.name,
                "expiry": expiry.isoformat(),
                "snapshot_time": self.snapshot_time(file),
                "expired": expiry <= date.today(),
            })
        return sorted(snapshots, key=lambda s: (s["snapshot_time"] or "", s["filename"]), reverse=True)

    def find_option_chain(self, expiry_date=None):
        snapshots = [s for s in self.available_snapshots() if not s["expired"]]
        if expiry_date is not None:
            if expiry_date <= date.today():
                raise ValueError("Select an unexpired contract. Expiry-day and expired scans are not supported.")
            snapshots = [s for s in snapshots if s["expiry"] == expiry_date.isoformat()]
        if not snapshots:
            raise ValueError("No matching unexpired option-chain CSV found in Input. Download your chosen later-expiry chain first.")
        # With several downloads for the same expiry, use the latest filename timestamp.
        return self.input_dir / snapshots[0]["filename"]

    def extract_expiry(self, csv_file):
        expiry = self._extract_expiry_from_name(Path(csv_file).name)
        if expiry is None:
            raise ValueError("CSV filename must include _YYYY-MM-DD_option_chain.")
        return expiry

    def get_trading_date(self):
        today = date.today()
        if today.weekday() == 5:
            today += timedelta(days=2)
        elif today.weekday() == 6:
            today += timedelta(days=1)
        return today

    def get_dte(self, expiry, trading_day):
        return (expiry - trading_day).days

    def get_spot_price_and_vix(self):
        from data_provider import fetch_spot_and_vix
        data = fetch_spot_and_vix(self.input_dir.parent)
        # Never overwrite usable values with a failed/partial API response.
        self.update_config_values({"SpotPrice": data["NIFTY 50"], "VIX": data["INDIA VIX"]})
        return data

    def update_config_values(self, values):
        workbook = load_workbook(self.config_file)
        try:
            sheet = workbook["CONFIG"]
            existing = {sheet.cell(row, 1).value: row for row in range(2, sheet.max_row + 1)}
            for key, value in values.items():
                row = existing.get(key, sheet.max_row + 1)
                sheet.cell(row, 1, key)
                sheet.cell(row, 2, value)
            atomic_workbook(self.config_file, workbook)
        finally:
            workbook.close()
