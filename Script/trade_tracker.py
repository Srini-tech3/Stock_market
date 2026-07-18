import pandas as pd


class TradeTracker:
    """Export strategy results to Excel workbooks."""

    def __init__(self, output_dir):
        self.output_dir = output_dir

    def export_strategy_results(self, bull_put_df, bear_call_df, expiry_date=None, file_name=None):
        if expiry_date is not None:
            expiry_str = expiry_date.isoformat() if hasattr(expiry_date, "isoformat") else str(expiry_date)
            if file_name is None:
                file_name = f"strategy_results_{expiry_str}.xlsx"
        else:
            file_name = file_name or "strategy_results.xlsx"

        columns_to_exclude = [
            "WingWidth",
            "SellBid",
            "SellAsk",
            "BuyBid",
            "BuyAsk",
            "SellIV",
            "BuyIV",
            "SellDelta",
            "BuyDelta",
            "SellTheta",
            "BuyTheta",
            "SellVega",
            "BuyVega",
            "SellPOP",
            "BuyPOP",
            "SellSpreadPct",
            "BuySpreadPct",
            "SellOI",
            "BuyOI",
            "SellVolume",
            "BuyVolume",
            "SpreadWidth",
            "NetVega",
            "LiquidityScore",
            "CreditEfficiency",
            "SafetyMargin",
        ]

        bull_put_report = bull_put_df.copy()
        bear_call_report = bear_call_df.copy()

        if expiry_date is not None:
            expiry_str = expiry_date.isoformat() if hasattr(expiry_date, "isoformat") else str(expiry_date)
            bull_put_report["ExpiryDate"] = expiry_str
            bear_call_report["ExpiryDate"] = expiry_str

        if "Rank" in bull_put_report.columns:
            bull_put_report = bull_put_report.sort_values("Rank").head(2)
        if "Rank" in bear_call_report.columns:
            bear_call_report = bear_call_report.sort_values("Rank").head(2)

        bull_put_report = bull_put_report.drop(
            columns=[col for col in columns_to_exclude if col in bull_put_report.columns],
            errors="ignore",
        )
        bear_call_report = bear_call_report.drop(
            columns=[col for col in columns_to_exclude if col in bear_call_report.columns],
            errors="ignore",
        )

        if "Rank" in bull_put_report.columns and "ExpiryDate" in bull_put_report.columns:
            cols = list(bull_put_report.columns)
            expiry_index = cols.index("ExpiryDate")
            cols.insert(cols.index("Rank") + 1, cols.pop(expiry_index))
            bull_put_report = bull_put_report[cols]

        if "Rank" in bear_call_report.columns and "ExpiryDate" in bear_call_report.columns:
            cols = list(bear_call_report.columns)
            expiry_index = cols.index("ExpiryDate")
            cols.insert(cols.index("Rank") + 1, cols.pop(expiry_index))
            bear_call_report = bear_call_report[cols]

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / file_name

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            bull_put_report.to_excel(writer, sheet_name="BullPut", index=False)
            bear_call_report.to_excel(writer, sheet_name="BearCall", index=False)

        return output_file