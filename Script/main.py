import pandas as pd

from config import ConfigManager
from option_chain import OptionChain
from market_context import MarketContext
from analyzer import Analyzer
from scorer import OptionScorer
from strategies import StrategyEngine
from trade_tracker import TradeTracker


def main():

    #----------------------------------------------------
    # Load Config
    #----------------------------------------------------
    config_manager = ConfigManager()
    config = config_manager.load_config()
    csv_file = config_manager.find_option_chain()
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

    # ----------------------------------------------------
    # ANALYZER
    # ----------------------------------------------------
    analyzer = Analyzer(oc.df, context)

    df = analyzer.run()
    print("ANALYZED OPTION CHAIN")

    # ----------------------------------------------------
    # SCORER
    # ----------------------------------------------------   
    scorer = OptionScorer(df, context)
    df = scorer.run()
    # ----------------------------------------------------
    # STRATEGY ENGINE
    # ----------------------------------------------------
    strategy_engine = StrategyEngine(df, context)
    bull_put_df, bear_call_df = strategy_engine.run()

    #----------------------------------------------------
    # Save Output
    #----------------------------------------------------
    tracker = TradeTracker(config_manager.output_dir)
    output_file = tracker.export_strategy_results(
        bull_put_df,
        bear_call_df,
        expiry_date=context.expiry_date,
    )

    print(f"\nOption strategy results exported created to: {output_file}")


if __name__ == "__main__":
    main()