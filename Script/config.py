from pathlib import Path
from datetime import date, timedelta
from openpyxl import load_workbook
import pandas as pd
import re


class ConfigManager:
    """Manage project configuration paths and option-chain metadata."""

    def __init__(
        self,
        input_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        config_file: Path | str | None = None,
    ):
        self.input_dir = Path(input_dir or "E:/StockMarket_Project/OptionAnalyzer/Input")
        self.output_dir = Path(output_dir or "E:/StockMarket_Project/OptionAnalyzer/Output")
        self.config_file = Path(config_file or self.input_dir / "Config.xlsx")

    def load_config(self):
        df = pd.read_excel(self.config_file, sheet_name="CONFIG")
        return dict(zip(df["Parameter"], df["Value"]))

    def find_option_chain(self):
        files = list(self.input_dir.glob("*.csv"))

        if len(files) == 0:
            raise FileNotFoundError("No CSV file found inside Input folder.")

        if len(files) > 1:
            raise Exception("Multiple CSV files found. Keep only one.")

        return files[0]

    def extract_expiry(self, csv_file):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", csv_file.name)

        if not match:
            raise Exception("Unable to detect expiry date from filename.")

        return pd.to_datetime(match.group(1)).date()

    def get_trading_date(self):
        today = date.today()

        if today.weekday() == 5:
            today += timedelta(days=2)

        elif today.weekday() == 6:
            today += timedelta(days=1)

        return today

    def get_dte(self, expiry, trading_day):
        return (expiry - trading_day).days

    def update_config_values(self, values: dict):
        wb = load_workbook(self.config_file)
        ws = wb["CONFIG"]

        existing = {}

        for row in range(2, ws.max_row + 1):
            parameter = ws.cell(row=row, column=1).value
            existing[parameter] = row

        for key, value in values.items():
            if key in existing:
                row = existing[key]
                ws.cell(row=row, column=2).value = value
            else:
                row = ws.max_row + 1
                ws.cell(row=row, column=1).value = key
                ws.cell(row=row, column=2).value = value

        wb.save(self.config_file)