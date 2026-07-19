import numpy as np
import pandas as pd


#-------------------------------------------------------
# Strategy Engine
#-------------------------------------------------------
class StrategyEngine:

    def __init__(self, df, context):
        self.df = df.copy()
        self.context = context

        self.wing_width = context.wing_width
        self.lot_size = context.lot_size

    def _empty_spread_dataframe(self):
        return pd.DataFrame(columns=[
            "Strategy",
            "SellStrike",
            "BuyStrike",
            "WingWidth",
            "SellPremium",
            "BuyPremium",
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
        ])

    #-------------------------------------------------------
    # Get row by strike
    #-------------------------------------------------------
    def _get_row(self, strike):
        rows = self.df[self.df["Strike"] == strike]

        if rows.empty:
            return None

        return rows.iloc[0]
    
    #-------------------------------------------------------
    # Generate Bull Put Spreads
    #-------------------------------------------------------
    def generate_bull_put_spreads(self):
        spreads = []

        sell_candidates = self.df[self.df["PutReady"] == True]

        for _, sell in sell_candidates.iterrows():
            sell_strike = sell["Strike"]
            buy_strike = sell_strike - self.wing_width
            buy = self._get_row(buy_strike)

            if buy is None:
                continue

            spreads.append({

                "Strategy": "Bull Put",

                # Strikes
                "SellStrike": sell_strike,
                "BuyStrike": buy_strike,
                "WingWidth": self.wing_width,

                # Premium
                "SellPremium": sell["PutLTP"],
                "BuyPremium": buy["PutLTP"],

                # Bid / Ask
                "SellBid": sell["PutBid"],
                "SellAsk": sell["PutAsk"],
                "BuyBid": buy["PutBid"],
                "BuyAsk": buy["PutAsk"],

                # IV
                "SellIV": sell["IV"],
                "BuyIV": buy["IV"],

                # Greeks
                "SellDelta": sell["PutDelta"],
                "BuyDelta": buy["PutDelta"],

                "SellTheta": sell["PutTheta"],
                "BuyTheta": buy["PutTheta"],

                "SellVega": sell["PutVega"],
                "BuyVega": buy["PutVega"],

                # POP
                "SellPOP": sell["PutPOP"],
                "BuyPOP": buy["PutPOP"],

                # Bid-Ask Spread
                "SellSpreadPct": sell["PutSpreadPct"],
                "BuySpreadPct": buy["PutSpreadPct"],

                # Liquidity
                "SellOI": sell["PutOI"],
                "BuyOI": buy["PutOI"],

                "SellVolume": sell["PutVolume"],
                "BuyVolume": buy["PutVolume"]

            })

        if not spreads:
            return self._empty_spread_dataframe()

        return pd.DataFrame(spreads)
    
    #-------------------------------------------------------
    # Generate Bear Call Spreads
    #-------------------------------------------------------
    def generate_bear_call_spreads(self):
        spreads = []

        sell_candidates = self.df[self.df["CallReady"] == True]

        for _, sell in sell_candidates.iterrows():
            sell_strike = sell["Strike"]
            buy_strike = sell_strike + self.wing_width
            buy = self._get_row(buy_strike)

            if buy is None:
                continue

            spreads.append({

                "Strategy": "Bear Call",

                # Strikes
                "SellStrike": sell_strike,
                "BuyStrike": buy_strike,
                "WingWidth": self.wing_width,

                # Premium
                "SellPremium": sell["CallLTP"],
                "BuyPremium": buy["CallLTP"],

                # Bid / Ask
                "SellBid": sell["CallBid"],
                "SellAsk": sell["CallAsk"],
                "BuyBid": buy["CallBid"],
                "BuyAsk": buy["CallAsk"],

                # IV
                "SellIV": sell["IV"],
                "BuyIV": buy["IV"],

                # Greeks
                "SellDelta": sell["CallDelta"],
                "BuyDelta": buy["CallDelta"],

                "SellTheta": sell["CallTheta"],
                "BuyTheta": buy["CallTheta"],

                "SellVega": sell["CallVega"],
                "BuyVega": buy["CallVega"],

                # POP
                "SellPOP": sell["CallPOP"],
                "BuyPOP": buy["CallPOP"],

                # Bid-Ask Spread
                "SellSpreadPct": sell["CallSpreadPct"],
                "BuySpreadPct": buy["CallSpreadPct"],

                # Liquidity
                "SellOI": sell["CallOI"],
                "BuyOI": buy["CallOI"],

                "SellVolume": sell["CallVolume"],
                "BuyVolume": buy["CallVolume"]

            })

        if not spreads:
            return self._empty_spread_dataframe()

        return pd.DataFrame(spreads)
    
    # -------------------------------------------------------
    # Calculate Strategy Metrics
    # -------------------------------------------------------
    def calculate_metrics(self, spread_df):

        if spread_df is None:
            return pd.DataFrame()

        if spread_df.empty:
            return spread_df

        df = spread_df.copy()

        df["NetCredit"] = (
            df["SellPremium"]
            - df["BuyPremium"]
        )

        df["SpreadWidth"] = (
            df["SellStrike"]
            - df["BuyStrike"]
        ).abs()

        df["MaxProfit"] = (
            df["NetCredit"]
            * self.lot_size
        )

        df["MaxLoss"] = (
            (
                df["SpreadWidth"]
                - df["NetCredit"]
            )
            * self.lot_size
        )
        
        df["BreakEven"] = None
        bull_mask = df["Strategy"] == "Bull Put"

        df.loc[bull_mask, "BreakEven"] = (
            df.loc[bull_mask, "SellStrike"]
            -
            df.loc[bull_mask, "NetCredit"]
        )       
        
        bear_mask = df["Strategy"] == "Bear Call"

        df.loc[bear_mask, "BreakEven"] = (
            df.loc[bear_mask, "SellStrike"]
            +
            df.loc[bear_mask, "NetCredit"]
        )

        df["NetDelta"] = (
            df["SellDelta"]
            -
            df["BuyDelta"]
        )

        df["NetTheta"] = (
            df["SellTheta"]
            -
            df["BuyTheta"]
        )
        df["NetVega"] = (
            df["SellVega"]
            -
            df["BuyVega"]
        )
        df["EstimatedPOP"] = (
            1
            -
            abs(df["SellDelta"])
        ) * 100
        df["ReturnOnRisk"] = (
            df["MaxProfit"]
            /
            df["MaxLoss"]
        ) * 100
        
        round_cols = [
            "NetCredit",
            "MaxProfit",
            "MaxLoss",
            "BreakEven",
            "NetDelta",
            "NetTheta",
            "NetVega",
            "EstimatedPOP",
            "ReturnOnRisk",
        ]

        df[round_cols] = df[round_cols].round(2)
        return df
    
    #-------------------------------------------------------
    # Quality Metrics
    #-------------------------------------------------------
    def calculate_quality_metrics(self, spread_df):

        if spread_df is None:
            return pd.DataFrame()

        if spread_df.empty:
            return spread_df.copy()

        df = spread_df.copy()

        df["LiquidityScore"] = (
            df["SellOI"] + df["BuyOI"]
        ) / 2

        df["CreditEfficiency"] = (
            df["NetCredit"] /
            df["SpreadWidth"]
        ) * 100

        df["SafetyMargin"] = np.where(
            df["Strategy"] == "Bull Put",
            self.context.spot_price - df["BreakEven"],
            df["BreakEven"] - self.context.spot_price
        )

        return df
    
    #-------------------------------------------------------
    # Filter Strategies
    #-------------------------------------------------------
    def filter_strategies(self, spread_df):

        if spread_df is None:
            return pd.DataFrame()

        if spread_df.empty:
            return spread_df.copy()

        df = spread_df.copy()

        df = df[df["EstimatedPOP"] >= self.context.min_pop]

        df = df[df["NetCredit"] >= getattr(self.context, "minimum_credit", 0)]

        df = df[df["ReturnOnRisk"] >= getattr(self.context, "minimum_ror", 0)]

        df = df[df["MaxLoss"] <= self.context.max_capital_per_trade]

        return df.reset_index(drop=True)

    #-------------------------------------------------------
    # Rank Strategies
    #-------------------------------------------------------
    def rank_strategies(self, spread_df):

        if spread_df is None:
            return pd.DataFrame()

        if spread_df.empty:
            return spread_df.copy()

        df = spread_df.copy()

        df = df.sort_values(
            by=[
                "EstimatedPOP",
                "CreditEfficiency",
                "ReturnOnRisk",
                "SafetyMargin",
                "LiquidityScore"
            ],
            ascending=[
                False,
                False,
                False,
                False,
                False
            ]
        )

        df.insert(0, "Rank", range(1, len(df) + 1))

        return df.reset_index(drop=True)
    
    #-------------------------------------------------------
    # Add Recommendation
    #-------------------------------------------------------
    def add_recommendation(self, spread_df):

        if spread_df is None:
            return pd.DataFrame()

        if spread_df.empty:
            return spread_df

        df = spread_df.copy()

        conditions = [
            df["Rank"] == 1,
            df["Rank"] == 2,
            df["Rank"] == 3,
        ]

        choices = [
            5,
            5,
            3,
        ]

        df["Recommendation"] = np.select(
            conditions,
            choices,
            default=2
        )

        return df
    #-------------------------------------------------------
    # Run Strategy Engine
    #-------------------------------------------------------
    def run(self):
        bull_put_df = self.generate_bull_put_spreads()
        bear_call_df = self.generate_bear_call_spreads()

        bull_put_df = self.calculate_metrics(bull_put_df)
        bear_call_df = self.calculate_metrics(bear_call_df)

        bull_put_df = self.calculate_quality_metrics(bull_put_df)
        bear_call_df = self.calculate_quality_metrics(bear_call_df)

        bull_put_df = self.filter_strategies(bull_put_df)
        bear_call_df = self.filter_strategies(bear_call_df)

        bull_put_df = self.rank_strategies(bull_put_df)
        bear_call_df = self.rank_strategies(bear_call_df)

        bull_put_df = self.add_recommendation(bull_put_df)
        bear_call_df = self.add_recommendation(bear_call_df)

        return bull_put_df, bear_call_df