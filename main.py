from AlgorithmImports import *
import numpy as np

class MNQ_Flush_Engine(QCAlgorithm):
    def Initialize(self):
        # 1. Core Engine Runtime Settings
        self.SetStartDate(2023, 1, 1)   
        self.SetCash(10000)             
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # 2. Dependency Injection: Stripping Proprietary Edge
        # (These pull safely from your local config.json file)
        self.tp_atr_mult = self.GetParameter("tp_atr_mult", 3.150)
        self.sl_atr_mult = self.GetParameter("sl_atr_mult", 2.250)
        self.max_daily_loss = self.GetParameter("max_usd_daily_loss", 79.0)
        
        # 3. High-Fidelity Asset Subscription ($MNQ Front Month Futures)
        self.future = self.AddFuture(Futures.Indices.NASDAQ100Micro, Resolution.Minute)
        self.future.SetFilter(lambda x: x.FrontMonth().OnlyApplyWithFilter(True))
        self.symbol = self.future.Symbol

        # 4. Indicators & State Tracking
        self.atr = self.ATR(self.symbol, 14, MovingAverageType.Wilders, Resolution.Minute)
        self.bars_since_entry = 0
        self.closed_daily_equity = self.Portfolio.TotalPortfolioValue

        # Schedule Daily Circuit Breakers
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.At(9, 30), self.ResetDailyMetrics)
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.At(15, 45), self.EODFlush)

        self.SetWarmUp(50, Resolution.Minute)

    def ResetDailyMetrics(self):
        self.closed_daily_equity = self.Portfolio.TotalPortfolioValue

    def EODFlush(self):
        if self.Portfolio.Invested:
            self.Liquidate(self.symbol, "EOD Hard Flatten")

    def OnData(self, slice):
        if self.IsWarmingUp or not self.atr.IsReady:
            return

        # Track bars since entry for time-based exits
        if self.Portfolio.Invested:
            self.bars_since_entry += 1
        else:
            self.bars_since_entry = 0

        # Daily loss circuit breaker check
        current_daily_realized = self.Portfolio.TotalPortfolioValue - self.Portfolio.TotalUnrealizedProfit - self.closed_daily_equity
        if current_daily_realized <= -self.max_daily_loss and self.Portfolio.Invested:
            self.Liquidate(self.symbol, "Daily Circuit Breaker Hit")
            return

        # Execution logic goes here
        # Example: Use self.tp_atr_mult and self.sl_atr_mult for bracket orders