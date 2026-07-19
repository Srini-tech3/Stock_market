import argparse
from datetime import datetime

import pandas as pd

from config import ConfigManager
from option_chain import OptionChain
from market_context import MarketContext
from analyzer import Analyzer
from scorer import OptionScorer
from strategies import StrategyEngine
from trade_tracker import TradeTracker


def parse_args():
    parser = argparse.ArgumentParser(description="Run option strategy scanning and generate reports.")
    parser.add_argument(
        "--expiry",
        "-e",
        help="Expiry date to select the matching option chain CSV file (YYYY-MM-DD).",
        required=False,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    expiry_arg = None

    if args.expiry:
        expiry_arg = datetime.strptime(args.expiry, "%Y-%m-%d").date()

    #----------------------------------------------------
    # Load Config
    #----------------------------------------------------
    config_manager = ConfigManager()
    config = config_manager.load_config()
    csv_file = config_manager.find_option_chain(expiry_arg)
    expiry = config_manager.extract_expiry(csv_file)
    trading_day = config_manager.get_trading_date()
    dte = config_manager.get_dte(expiry, trading_day)

    context = MarketContext(

        spot_price=float(config["SpotPrice"]),
        vix=float(config["VIX"]),
        trend=config["Trend"],
        cpr_width=config["CPRWidth"],

        trading_date=trading_day,
        expiry_date=expiry,
        dte=dte,

        lot_size=int(config["LotSize"]),
        wing_width=int(config["WingWidth"]),
        capital=float(config["AvailableCapital"]),

        min_pop=float(config["MinPOP"]),
        min_delta=float(config["MinDelta"]),
        max_delta=float(config["MaxDelta"]),
        min_oi=int(config["MinOI"]),
        min_volume=int(config["MinVolume"]),
        max_bid_ask=float(config["MaxBidAskPct"]),
        max_spread_points=float(config["MaxSpreadPoints"]),
        max_capital_per_trade=float(config["MaxCapitalPerTrade"]),
        minimum_credit=float(config.get("MinimumCredit", 0)),
        minimum_ror=float(config.get("MinimumROR", 0))

    )

    #----------------------------------------------------
    # Update Config.xlsx
    #----------------------------------------------------
    config_manager.update_config_values({
        "ExpiryDate": str(expiry),
        "TradingDate": str(trading_day),
        "DTE": dte
    })
    print(f"\nUpdated Config.xlsx with Expiry Date: {expiry}, Trading Date: {trading_day}, DTE: {dte}")

    # ----------------------------------------------------
    # OPTION CHAIN
    # ----------------------------------------------------
    oc = OptionChain(csv_file)
    oc.load()
    oc.clean()
    oc.rename_columns()
    oc.convert_numeric()
    oc.validate()
    print(f"\nOption Chain DataFrame has {len(oc.df)} rows and {len(oc.df.columns)} columns")
    print(f"After OptionChain validate, columns: {list(oc.df.columns)}")
    print(f"OptionChain sample rows:\n{oc.df.head(3)}")

    # ----------------------------------------------------
    # ANALYZER
    # ----------------------------------------------------
    analyzer = Analyzer(oc.df, context)
    df = analyzer.run()
    print(f"Analyzer complete, dataframe shape: {df.shape}")
    print(f"Analyzer sample rows:\n{df.head(3)}")
    print("ANALYZED OPTION CHAIN")

    # ----------------------------------------------------
    # SCORER
    # ----------------------------------------------------   
    scorer = OptionScorer(df, context)
    df = scorer.run()
    print(f"Scorer complete, dataframe shape: {df.shape}")
    print(f"Scorer sample rows:\n{df.head(3)}")
    # ----------------------------------------------------
    # STRATEGY ENGINE
    # ----------------------------------------------------
    strategy_engine = StrategyEngine(df, context)
    bull_put_df, bear_call_df = strategy_engine.run()
    print(f"Strategy engine complete: bull_put={len(bull_put_df)} rows, bear_call={len(bear_call_df)} rows")
    print(f"Bull Put sample:\n{bull_put_df.head(3)}")
    print(f"Bear Call sample:\n{bear_call_df.head(3)}")

    #----------------------------------------------------
    # Save Output
    #----------------------------------------------------
    tracker = TradeTracker(config_manager.output_dir)
    output_file = tracker.export_strategy_results(
        bull_put_df,
        bear_call_df,
        expiry_date=context.expiry_date,
    )

    journal_file = tracker.export_journal_tracker(
        bull_put_df,
        bear_call_df,
        expiry_date=context.expiry_date,
        capital=context.capital,
    )

    print(f"\nOption strategy results exported created to: {output_file}")
    print(f"Journal tracker exported created to: {journal_file}")
    print(f"\nResult saved to JSON file.")
    print("\nOption strategy scanning and report generation completed successfully.")


if __name__ == "__main__":
    main()