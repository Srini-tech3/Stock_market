from SmartApi import SmartConnect
import pyotp
import warnings
warnings.filterwarnings('ignore')

API_KEY = "FRfnmfua"
USERNAME = "AABY695968"
PASSWORD = "3571"
TOTP_TOKEN = "YNJD5GCGCJLGK2V5WGTG6M6MOA"

EXCHANGE = "NSE"
MARKET_ITEMS = [
    ("NIFTY 50", "99926000"),
    ("INDIA VIX", "99926017"),
]

smart_api = SmartConnect(api_key=API_KEY)
totp = pyotp.TOTP(TOTP_TOKEN).now()

if smart_api.generateSession(USERNAME, PASSWORD, totp).get('status'):
    for symbol, token in MARKET_ITEMS:
        ltp_data = smart_api.ltpData(EXCHANGE, symbol, token)
        price = ltp_data.get('data', {}).get('ltp') if isinstance(ltp_data.get('data'), dict) else None
        print(f"{symbol}: {price if price is not None else 'Unable to fetch spot price'}")
else:
    print("Login failed")
