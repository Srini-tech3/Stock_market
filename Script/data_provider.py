"""Optional SmartAPI spot/VIX refresh. CSV scanning needs no broker credentials."""
import math
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from app_support import log_event


class MarketDataError(RuntimeError):
    pass


def fetch_spot_and_vix(project_root):
    load_dotenv(Path(project_root) / ".env", override=False)
    names = ("ANGEL_API_KEY", "ANGEL_CLIENT_ID", "ANGEL_PIN", "ANGEL_TOTP_SECRET")
    credentials = [os.environ.get(name, "").strip() for name in names]
    if not all(credentials):
        raise MarketDataError("SmartAPI credentials are not configured. Use CSV snapshot mode or configure .env.")
    # The local SDK lives alongside Script when running from source.
    source_root = str(Path(__file__).resolve().parent.parent)
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    from SmartApi import SmartConnect
    import pyotp

    log_event("broker_authentication_started")
    try:
        api_key, client_id, pin, secret = credentials
        try:
            totp = pyotp.TOTP(secret).now()
        except Exception:
            raise MarketDataError("Invalid SmartAPI TOTP secret. Check your local .env configuration.") from None
        broker = SmartConnect(api_key=api_key, timeout=7, debug=False)
        session = broker.generateSession(client_id, pin, totp)
        if not isinstance(session, dict) or not session.get("status"):
            raise MarketDataError("SmartAPI authentication failed. Check credentials/session and retry.")
        log_event("broker_authentication_succeeded")
        values = {}
        for symbol, token in (("NIFTY 50", "99926000"), ("INDIA VIX", "99926017")):
            response = broker.ltpData("NSE", symbol, token)
            data = response.get("data") if isinstance(response, dict) else None
            if not isinstance(data, dict) or not response.get("status"):
                raise MarketDataError(f"SmartAPI {symbol} quote unavailable. Check API/session or rate limits.")
            try:
                price = float(data["ltp"])
            except (KeyError, TypeError, ValueError):
                raise MarketDataError(f"SmartAPI returned an invalid {symbol} price.") from None
            if not math.isfinite(price) or price <= 0:
                raise MarketDataError(f"SmartAPI returned an invalid {symbol} price.")
            values[symbol] = price
            log_event("market_quote_received", instrument=symbol)
        return values
    except MarketDataError:
        log_event("broker_request_failed")
        raise
    except requests.exceptions.Timeout:
        raise MarketDataError("SmartAPI request timed out. Retry or use CSV snapshot mode.") from None
    except requests.exceptions.RequestException:
        raise MarketDataError("SmartAPI network request failed. Check connectivity and retry.") from None
    except Exception:
        # Broker exceptions may contain request credentials. Do not return/log their text.
        raise MarketDataError("SmartAPI refresh failed (API/session/rate-limit error). Retry or use CSV snapshot mode.") from None
