"""CSV-first practice scanning, preserving the existing workbook rulebook and ranking."""
import argparse
import math
import threading
from datetime import date, datetime

from analyzer import Analyzer
from app_support import configure_logging, log_event, utc_now
from config import ConfigManager
from market_context import MarketContext
from option_chain import OptionChain
from scorer import OptionScorer
from strategies import StrategyEngine
from trade_tracker import TradeTracker

_SCAN_LOCK = threading.Lock()


class AnalysisBusy(RuntimeError):
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="Scan an uploaded NIFTY CSV for Sensibull practice trades.")
    parser.add_argument("--expiry", "-e", help="Exact CSV contract expiry (YYYY-MM-DD); defaults to latest unexpired upload.")
    parser.add_argument("--market-source", choices=("csv", "live", "config"), default="csv",
                        help="csv: snapshot spot; live: optional SmartAPI spot/VIX; config: manually configured values.")
    return parser.parse_args()


def run_analysis(expiry_date=None, market_source="csv", config_manager=None):
    if market_source not in ("csv", "live", "config"):
        raise ValueError("Market source must be csv, live or config.")
    expiry_arg = None
    if expiry_date is not None:
        if not isinstance(expiry_date, str) or not expiry_date:
            raise ValueError("Expiry must be a date in YYYY-MM-DD format.")
        try:
            expiry_arg = date.fromisoformat(expiry_date)
        except ValueError:
            raise ValueError("Expiry must be a date in YYYY-MM-DD format.") from None
    manager = config_manager or ConfigManager()
    # Validate the upload and rulebook before touching the broker or publishing outputs.
    csv_file = manager.find_option_chain(expiry_arg)
    expiry = manager.extract_expiry(csv_file)
    trading_day = manager.get_trading_date()
    dte = manager.get_dte(expiry, trading_day)
    if dte <= 0:
        raise ValueError("The selected contract has expired or has no remaining trading days.")
    config = manager.load_config()
    if not _SCAN_LOCK.acquire(blocking=False):
        raise AnalysisBusy("An analysis is already running. Wait for it to finish.")
    try:
        configure_logging(manager.output_dir.parent)
        log_event("analysis_started", expiry=expiry.isoformat(), filename=csv_file.name, market_source=market_source)
        chain = OptionChain(csv_file)
        chain.load()
        chain.clean()
        chain.rename_columns()
        chain.convert_numeric()
        chain.validate()
        warnings = []
        snapshot_time = manager.snapshot_time(csv_file)
        if snapshot_time is None:
            warnings.append("CSV quote time is unknown. The filename does not contain a snapshot timestamp.")
        elif datetime.fromisoformat(snapshot_time).date() != date.today():
            warnings.append("CSV filename timestamp is not today. These are historical/delayed practice observations.")
        warnings.append("CSV prices are snapshots, not streaming quotes. Verify contracts and fills in Sensibull.")
        if market_source == "live":
            from data_provider import fetch_spot_and_vix
            quotes = fetch_spot_and_vix(manager.input_dir.parent)
            spot, vix = quotes["NIFTY 50"], quotes["INDIA VIX"]
            spot_source, vix_source = "SmartAPI refresh", "SmartAPI refresh"
            warnings.append("SmartAPI spot/VIX and uploaded option quotes are from separate snapshots.")
        elif market_source == "csv":
            spot = chain.snapshot_underlying("Spot")
            if spot is None:
                raise ValueError("CSV has no usable spot intrinsic values. Choose manual Config.xlsx mode and update SpotPrice first.")
            vix = float(config["VIX"])
            spot_source, vix_source = "CSV intrinsic values", "Config.xlsx (manual)"
        else:
            spot, vix = float(config["SpotPrice"]), float(config["VIX"])
            spot_source = vix_source = "Config.xlsx (manual)"
            warnings.append("Spot and VIX are manual configuration values. Confirm they match the uploaded chain.")
        if not math.isfinite(spot) or spot <= 0:
            raise ValueError("A positive finite spot price is required.")
        if not math.isfinite(vix) or vix <= 0:
            raise ValueError("A positive finite VIX is required in Config.xlsx or via SmartAPI.")
        try:
            futures = chain.snapshot_underlying("Future")
        except ValueError:
            futures = None
            warnings.append("CSV futures intrinsic values are inconsistent; futures overview is unavailable.")
        context = MarketContext(
            spot_price=spot, vix=vix, trend=config.get("Trend", "Not configured"),
            cpr_width=config.get("CPRWidth", "Not configured"),
            trading_date=trading_day, expiry_date=expiry, dte=dte,
            lot_size=int(config["LotSize"]), wing_width=int(config["WingWidth"]),
            capital=float(config["AvailableCapital"]), min_pop=float(config["MinPOP"]),
            min_delta=float(config["MinDelta"]), max_delta=float(config["MaxDelta"]),
            min_oi=int(config["MinOI"]), min_volume=int(config["MinVolume"]),
            max_bid_ask=float(config["MaxBidAskPct"]), max_spread_points=float(config["MaxSpreadPoints"]),
            max_capital_per_trade=float(config["MaxCapitalPerTrade"]),
            minimum_credit=float(config.get("MinimumCredit", 0)), minimum_ror=float(config.get("MinimumROR", 0)),
        )
        analyzer = Analyzer(chain.df, context)
        scored = OptionScorer(analyzer.run(), context).run()
        bull_put, bear_call = StrategyEngine(scored, context).run()
        log_event("strategies_generated", bull_put=len(bull_put), bear_call=len(bear_call),
                  ready_puts=int(scored.PutReady.sum()), ready_calls=int(scored.CallReady.sum()))
        tracker = TradeTracker(manager.output_dir)
        output_file = tracker.export_strategy_results(bull_put, bear_call, expiry_date=expiry, publish_json=False)
        journal_file = tracker.export_journal_tracker(bull_put, bear_call, expiry_date=expiry, capital=context.capital)
        # Publish the dashboard snapshot only after successful report/journal writes.
        put_oi, call_oi = scored.PutOI.sum(min_count=1), scored.CallOI.sum(min_count=1)
        pcr = float(put_oi / call_oi) if call_oi > 0 and math.isfinite(put_oi) else None
        invalid_calls = int((~scored.CallDataValid).sum())
        invalid_puts = int((~scored.PutDataValid).sum())
        if invalid_calls or invalid_puts:
            warnings.append(f"Invalid/incomplete quote sides excluded: {invalid_calls} CE, {invalid_puts} PE. Unused fields may still be missing.")
        metadata = {
            "generated_at": utc_now(), "mode": "SENSIBULL PRACTICE", "data_status": "CSV SNAPSHOT",
            "source_file": csv_file.name, "snapshot_time": snapshot_time,
            "trading_date": trading_day.isoformat(), "dte": dte, "warnings": warnings,
            "market": {"spot": spot, "spot_source": spot_source, "vix": vix, "vix_source": vix_source,
                       "futures": futures, "futures_source": "CSV intrinsic values" if futures else None,
                       "futures_premium": round(futures - spot, 2) if futures else None,
                       "atm": int(analyzer.atm), "atm_iv": analyzer.atm_iv,
                       "expected_move": analyzer.expected_move, "pcr": round(pcr, 3) if pcr is not None else None,
                       "trend": context.trend, "cpr_width": context.cpr_width, "lot_size": context.lot_size},
            "rules": {key: config[key] for key in ConfigManager.NUMERIC_RULES if key not in ("SpotPrice", "VIX")},
            "ranking": "Separate rank per strategy: POP, credit efficiency, RoR, safety margin, then average OI (descending).",
            "pricing": "LTP reference premiums; estimated payoff before fees/slippage. POP is the existing short-delta proxy.",
            "journal_rows_added": tracker.journal_rows_added,
            "reports": {"strategies": output_file.name, "journal": journal_file.name},
            "option_chain": tracker._dataframe_to_records(scored),
        }
        for key in ("MinimumCredit", "MinimumROR"):
            metadata["rules"][key] = float(config.get(key, 0))
        payload = tracker._write_strategy_result_json(bull_put, bear_call, expiry, metadata)
        log_event("analysis_completed", expiry=expiry.isoformat(), journal_rows_added=tracker.journal_rows_added)
        return payload
    except Exception as error:
        # Only the class is logged; broker error text can contain secrets.
        log_event("analysis_failed", error_type=type(error).__name__)
        raise
    finally:
        _SCAN_LOCK.release()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        result = run_analysis(arguments.expiry, arguments.market_source)
        print(f"Scan complete: {len(result['bull_put'])} Bull Put / {len(result['bear_call'])} Bear Call opportunities.")
        print(f"Journal rows appended: {result['journal_rows_added']}. Files saved in {ConfigManager().output_dir}")
    except (ValueError, AnalysisBusy, PermissionError) as error:
        raise SystemExit(str(error))
