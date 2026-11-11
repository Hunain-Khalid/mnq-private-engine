# region imports
from AlgorithmImports import *
# endregion

class SingleHMASlopeFutureAlgorithm(QCAlgorithm):

    def initialize(self) -> None:
        # In-Sample (IS): 2014-01-01 to 2021-06-30
        # Out-of-Sample (OOS): 2024-07-01 to 2026-06-30
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2024, 6, 30)
        self.set_cash(1000000) 
        
        self.universe_settings.asynchronous = True
        self.settings.daily_consolidation_use_extended_market_hours = True
        
        self._future = self.add_future(
            Futures.Indices.SP_500_E_MINI,
            resolution=Resolution.MINUTE, 
            extended_market_hours=True,
            data_mapping_mode=DataMappingMode.LAST_TRADING_DAY, 
            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO, 
            contract_depth_offset=0
        )
        self._future.set_filter(0, 92)

        # 1. Trend Engine: Single Hull Moving Average (HMA) on Daily/Minute resolution
        self.hma_indicator = self.hma(self._future.symbol, 20, Resolution.DAILY)
        
        # 2. Volatility Gate: Average True Range (ATR) to filter out low-energy chop
        self.atr_indicator = self.atr(self._future.symbol, 14, MovingAverageType.SIMPLE, Resolution.DAILY)

        self.set_warm_up(30, Resolution.DAILY)

        # 3. Risk Management: 1% risk model with 50-point stop loss
        self.stop_loss_points = 50.0

        # Scheduled Execution & EOD Flat Rule
        self.schedule.on(
            self.date_rules.every_day(self._future.symbol),
            self.time_rules.after_market_open(self._future.symbol, 30),
            self.check_signals_and_trade
        )

        self.schedule.on(
            self.date_rules.every_day(self._future.symbol),
            self.time_rules.before_market_close(self._future.symbol, 15), # 3:45 PM EST EOD Rule
            self.liquidate_eod
        )
        
        self.last_hma_val = 0.0

    def on_data(self, slice: Slice) -> None:
        pass

    def check_signals_and_trade(self) -> None:
        if self.is_warming_up or not self.hma_indicator.is_ready or not self.atr_indicator.is_ready:
            return

        mapped_symbol = self._future.mapped
        if mapped_symbol is None:
            return

        if not self.securities[mapped_symbol].exchange.exchange_open:
            return

        current_hma = self.hma_indicator.current.value
        current_atr = self.atr_indicator.current.value
        current_quantity = self.portfolio[mapped_symbol].quantity

        if self.last_hma_val == 0.0:
            self.last_hma_val = current_hma
            return

        # 4. Single HMA Slope Direction (No lagging dual-indicator crossovers)
        hma_slope_positive = current_hma > self.last_hma_val
        hma_slope_negative = current_hma < self.last_hma_val

        # 5. Volatility Gate Check (Ensures market energy is active)
        volatility_confirmed = current_atr > 0

        # Calculate exact contract size for 1% portfolio risk
        target_quantity = self.calculate_risk_adjusted_volume(mapped_symbol)

        # 6. Execution Logic
        if hma_slope_positive and volatility_confirmed:
            if current_quantity <= 0:
                self.liquidate(mapped_symbol)
                self.market_order(mapped_symbol, target_quantity)
                self.log(f"BUY {target_quantity} {mapped_symbol.value} @ {self.time} | Single HMA Slope Positive")

        elif hma_slope_negative and volatility_confirmed:
            if current_quantity >= 0:
                self.liquidate(mapped_symbol)
                self.market_order(mapped_symbol, -target_quantity)
                self.log(f"SHORT -{target_quantity} {mapped_symbol.value} @ {self.time} | Single HMA Slope Negative")

        self.last_hma_val = current_hma

    def calculate_risk_adjusted_volume(self, symbol: Symbol) -> int:
        """Calculates contract size so that a stop-loss hit equals exactly 1% of equity."""
        risk_amount_usd = self.portfolio.total_portfolio_value * 0.01
        multiplier = self.securities[symbol].symbol_properties.contract_multiplier
        risk_per_contract = self.stop_loss_points * multiplier
        
        if risk_per_contract <= 0:
            return 1
            
        contracts_to_trade = int(risk_amount_usd // risk_per_contract)
        return max(1, contracts_to_trade)

    def liquidate_eod(self) -> None:
        """Forces all positions flat before the market close (3:45 PM EST) to eliminate overnight risk."""
        mapped_symbol = self._future.mapped
        if mapped_symbol and self.portfolio[mapped_symbol].invested:
            self.liquidate(mapped_symbol)
            self.log(f"EOD FLAT {mapped_symbol.value} @ {self.time} | Prop Firm EOD Rule Enforced")