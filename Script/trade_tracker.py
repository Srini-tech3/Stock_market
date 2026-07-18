import pandas as pd


class TradeTracker:
    """Export strategy results to Excel workbooks."""

    def __init__(self, output_dir):
        self.output_dir = output_dir

    def export_strategy_results(self, bull_put_df, bear_call_df, file_name="strategy_results.xlsx"):
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

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / file_name

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            bull_put_report.to_excel(writer, sheet_name="BullPut", index=False)
            bear_call_report.to_excel(writer, sheet_name="BearCall", index=False)

        return output_file