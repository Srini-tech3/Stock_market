"""Optional command-line SmartAPI quote check; never authenticates on import."""
from config import project_root
from data_provider import fetch_spot_and_vix, MarketDataError


if __name__ == "__main__":
    try:
        for symbol, price in fetch_spot_and_vix(project_root()).items():
            print(f"{symbol}: {price}")
    except MarketDataError as error:
        raise SystemExit(str(error))
