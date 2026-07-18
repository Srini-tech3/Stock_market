from dataclasses import dataclass
from datetime import date


@dataclass
class MarketContext:

    # Market
    spot_price: float
    vix: float
    trend: str
    cpr_width: str

    # Dates
    trading_date: date
    expiry_date: date
    dte: int

    # Trading
    lot_size: int
    wing_width: int
    capital: float

    # Filters
    min_pop: float
    min_delta: float
    max_delta: float
    min_oi: int
    min_volume: int
    max_bid_ask: float
    max_spread_points: float
    max_capital_per_trade: float
    minimum_credit: float = 0.0
    minimum_ror: float = 0.0