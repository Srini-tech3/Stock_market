import numpy as np


class OptionScorer:

    def __init__(self, df, context):

        self.df = df
        self.ctx = context

    # -------------------------------------------------------
    # Bid / Ask Spread %
    # -------------------------------------------------------
    def calculate_spread(self):

        self.df["CallSpreadPct"] = np.where(
            self.df["CallAsk"] > 0,
            (
                (self.df["CallAsk"] - self.df["CallBid"])
                / self.df["CallAsk"]
            ) * 100,
            np.nan
        )

        self.df["PutSpreadPct"] = np.where(
            self.df["PutAsk"] > 0,
            (
                (self.df["PutAsk"] - self.df["PutBid"])
                / self.df["PutAsk"]
            ) * 100,
            np.nan
        )

        self.df["CallSpreadPct"] = self.df["CallSpreadPct"].round(2)
        self.df["PutSpreadPct"] = self.df["PutSpreadPct"].round(2)

    # -------------------------------------------------------
    # Delta Eligibility
    # -------------------------------------------------------
    def calculate_delta_filter(self):

        self.df["CallDeltaEligible"] = (
            self.df["CallDelta"].abs().between(
                self.ctx.min_delta,
                self.ctx.max_delta
            )
        )

        self.df["PutDeltaEligible"] = (
            self.df["PutDelta"].abs().between(
                self.ctx.min_delta,
                self.ctx.max_delta
            )
        )

    # -------------------------------------------------------
    # OTM Filter
    # -------------------------------------------------------
    def calculate_otm_filter(self):

        self.df["CallOTM"] = self.df["CallMoneyness"] == "OTM"

        self.df["PutOTM"] = self.df["PutMoneyness"] == "OTM"

    # -------------------------------------------------------
    # Theta Efficiency
    # -------------------------------------------------------
    def calculate_theta_efficiency(self):

        self.df["CallThetaEfficiency"] = np.where(
            self.df["CallDelta"].abs() > 0,
            abs(self.df["CallTheta"]) /
            self.df["CallDelta"].abs(),
            np.nan
        )

        self.df["PutThetaEfficiency"] = np.where(
            self.df["PutDelta"].abs() > 0,
            abs(self.df["PutTheta"]) /
            self.df["PutDelta"].abs(),
            np.nan
        )

        self.df["CallThetaEfficiency"] = (
            self.df["CallThetaEfficiency"].round(2)
        )

        self.df["PutThetaEfficiency"] = (
            self.df["PutThetaEfficiency"].round(2)
        )

    # -------------------------------------------------------
    # Liquidity Check
    # -------------------------------------------------------
    def calculate_liquidity(self):

        call_spread_ok = (
            (self.df["CallSpreadPct"] <= self.ctx.max_bid_ask)
            | (self.df["CallSpreadPct"] <= self.ctx.max_spread_points)
        )

        put_spread_ok = (
            (self.df["PutSpreadPct"] <= self.ctx.max_bid_ask)
            | (self.df["PutSpreadPct"] <= self.ctx.max_spread_points)
        )

        self.df["CallLiquid"] = (
            (self.df["CallOI"] >= self.ctx.min_oi)
            & (self.df["CallVolume"] >= self.ctx.min_volume)
            & call_spread_ok
        )

        self.df["PutLiquid"] = (
            (self.df["PutOI"] >= self.ctx.min_oi)
            & (self.df["PutVolume"] >= self.ctx.min_volume)
            & put_spread_ok
        )

    # -------------------------------------------------------
    # Final Option Ready Flag
    # -------------------------------------------------------
    def calculate_ready_flag(self):

        self.df["CallReady"] = (
            self.df["CallOTM"]
            &
            self.df["CallDeltaEligible"]
            &
            self.df["CallLiquid"]
        )

        self.df["PutReady"] = (
            self.df["PutOTM"]
            &
            self.df["PutDeltaEligible"]
            &
            self.df["PutLiquid"]
        )

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------
    def summary(self):

        print("\n" + "=" * 60)
        print("OPTION FILTER SUMMARY")
        print("=" * 60)
        print(f"Total Strikes           : {len(self.df)}")
        print(f"OTM Calls              : {self.df['CallOTM'].sum()}")
        print(f"OTM Puts               : {self.df['PutOTM'].sum()}")
        print(f"Delta Eligible Calls   : {self.df['CallDeltaEligible'].sum()}")
        print(f"Delta Eligible Puts    : {self.df['PutDeltaEligible'].sum()}")
        print(f"Liquid Calls           : {self.df['CallLiquid'].sum()}")
        print(f"Liquid Puts            : {self.df['PutLiquid'].sum()}")
        print(f"Ready Calls            : {self.df['CallReady'].sum()}")
        print(f"Ready Puts             : {self.df['PutReady'].sum()}")

    # -------------------------------------------------------
    # Run
    # -------------------------------------------------------
    def run(self):

        self.calculate_spread()
        self.calculate_otm_filter()
        self.calculate_delta_filter()
        self.calculate_theta_efficiency()
        self.calculate_liquidity()
        self.calculate_ready_flag()
        return self.df