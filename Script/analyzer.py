import numpy as np
import pandas as pd


class Analyzer:

    def __init__(self, df, context):

        self.df = df.copy()
        self.ctx = context

    # -------------------------------------------------------
    # Find ATM Strike
    # -------------------------------------------------------
    def calculate_atm(self):

        self.atm = min(
            self.df["Strike"],
            key=lambda x: abs(x - self.ctx.spot_price)
        )

        return self.atm

    # -------------------------------------------------------
    # Distance from ATM
    # -------------------------------------------------------
    def calculate_distance(self):

        self.df["DistanceFromATM"] = (
            self.df["Strike"] - self.atm
        )

        self.df["AbsDistance"] = (
            self.df["DistanceFromATM"].abs()
        )

    # -------------------------------------------------------
    # Get ATM IV
    # -------------------------------------------------------
    def calculate_atm_iv(self):

        atm_row = self.df[self.df["Strike"] == self.atm]

        if atm_row.empty:
            raise Exception("ATM strike not found.")

        self.atm_iv = float(atm_row.iloc[0]["IV"])

        return self.atm_iv
    
    # -------------------------------------------------------
    # Moneyness
    # -------------------------------------------------------
    def classify_moneyness(self):

        call_type = []
        put_type = []

        for strike in self.df["Strike"]:

            if strike == self.atm:

                call_type.append("ATM")
                put_type.append("ATM")

            elif strike < self.atm:

                call_type.append("ITM")
                put_type.append("OTM")

            else:

                call_type.append("OTM")
                put_type.append("ITM")

        self.df["CallMoneyness"] = call_type
        self.df["PutMoneyness"] = put_type

    # -------------------------------------------------------
    # Expected Move using ATM IV
    # -------------------------------------------------------
    def calculate_expected_move(self):

        iv = self.atm_iv / 100.0

        em = (
            self.ctx.spot_price
            * iv
            * np.sqrt(self.ctx.dte / 365)
        )

        self.expected_move = round(float(em), 2)

        lower = round(float(self.ctx.spot_price - em), 2)
        upper = round(float(self.ctx.spot_price + em), 2)

        self.expected_range = (lower, upper)

        self.df["InsideExpectedMove"] = self.df["Strike"].between(
            lower,
            upper
        )

    # -------------------------------------------------------
    # Market Summary
    # -------------------------------------------------------
    def market_summary(self):

        summary = {

            "Spot": self.ctx.spot_price,
            "ATM": self.atm,
            "ATM IV": self.atm_iv,
            "India VIX": self.ctx.vix,
            "DTE": self.ctx.dte,
            "OneSigmaMove": self.expected_move,
            "ExpectedRange": self.expected_range

        }

        return summary

    # -------------------------------------------------------
    # Run All
    # -------------------------------------------------------
    def run(self):

        self.calculate_atm()
        self.calculate_atm_iv()
        self.calculate_distance()
        self.classify_moneyness()
        self.calculate_expected_move()

        return self.df