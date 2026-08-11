# region imports
from AlgorithmImports import *
# endregion

class SingleHMASlopeFutureAlgorithm(QCAlgorithm):

    def initialize(self) -> None:
        # In-Sample (IS): 2012-01-01 to 2019-06-30
        # Out-of-Sample (OOS): 2019-07-01 to 2026-06-30
        self.set_start_date(2012, 1, 1)
        self.set_end_date(2019, 6, 30)
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

        # 1. Trend Engine: Single Hull Moving Average (HMA)
        self.hma_indicator = self.hma(self._future.symbol, 3, Resolution.MINUTE)
        
        # 2. Volatility Gate: Average True Range (ATR)
        self.atr_indicator = self.atr(self._future.symbol, 14, MovingAverageType.SIMPLE, Resolution.MINUTE)

        self.set_warm_up(30, Resolution.MINUTE)

        # 3. Asymmetric Risk Management Defaults (Long vs Short)
        self.long_stop_points = 60.0   # Wider berth for upward drift
        self.short_stop_points = 40.0  # Tighter control for short headwinds

        # 4. Runner (Sprinter) vs Lagger (Trend Rider) Parameters
        self.sprinter_target_points = 20.0  # Fast scalp target
        self.lagger_target_points = 90.0    # Macro trend target
        
        # Time-Stop Rule: Max minutes allowed in trade before forced time-exit
        self.sprinter_max_minutes = 20      # Quick exit if momentum stalls
        self.lagger_max_minutes = 120       # Gives the lagger massive time to run

        # Track trade entry times and legs
        self.trade_entry_times = {}
        self.last_hma_val = 0.0

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

        current_price = self.securities[mapped_symbol].price
        current_hma = self.hma_indicator.current.value
        current_atr = self.atr_indicator.current.value
        current_quantity = self.portfolio[mapped_symbol].quantity

        if self.last_hma_val == 0.0:
            self.last_hma_val = current_hma
            return

        # Time-Stop Check for existing open positions
        if current_quantity != 0 and mapped_symbol in self.trade_entry_times:
            entry_time = self.trade_entry_times[mapped_symbol]
            duration_minutes = (self.time - entry_time).total_seconds() / 60.0
            
            # If position has dragged past max allowed time without clean resolution, flatten
            if duration_minutes >= self.lagger_max_minutes:
                self.liquidate(mapped_symbol)
                self.log(f"TIME-STOP EXITED {mapped_symbol.value} @ {self.time} | Duration: {duration_minutes:.1f} mins")
                del self.trade_entry_times[mapped_symbol]
                return

        # Single HMA Slope Direction
        hma_slope_positive = current_hma > self.last_hma_val
        hma_slope_negative = current_hma < self.last_hma_val
        volatility_confirmed = current_atr > 0

        # Calculate exact risk-adjusted volume split
        total_target_qty = self.calculate_risk_adjusted_volume(mapped_symbol)
        
        # Split into Sprinter (Runner) and Lagger (Trend Rider) - e.g., 50/50 split or 1/3 vs 2/3
        sprinter_qty = max(1, total_target_qty // 2)
        lagger_qty = max(1, total_target_qty - sprinter_qty)

        # Execution Logic with Dual Legs & Asymmetric Stops
        if hma_slope_positive and volatility_confirmed:
            if current_quantity <= 0:
                self.liquidate(mapped_symbol)
                
                # Enter Long Leg 1 (Sprinter) & Leg 2 (Lagger)
                self.market_order(mapped_symbol, sprinter_qty)
                self.market_order(mapped_symbol, lagger_qty)
                
                # Set Bracket Orders (Asymmetric Long Stops & Distinct Targets)
                self.stop_market_order(mapped_symbol, -(sprinter_qty + lagger_qty), current_price - self.long_stop_points)
                self.limit_order(mapped_symbol, -sprinter_qty, current_price + self.sprinter_target_points)
                self.limit_order(mapped_symbol, -lagger_qty, current_price + self.lagger_target_points)
                
                self.trade_entry_times[mapped_symbol] = self.time
                self.log(f"BUY DUAL-LEG: Sprinter({sprinter_qty}) & Lagger({lagger_qty}) @ {current_price}")

        elif hma_slope_negative and volatility_confirmed:
            if current_quantity >= 0:
                self.liquidate(mapped_symbol)
                
                # Enter Short Leg 1 (Sprinter) & Leg 2 (Lagger)
                self.market_order(mapped_symbol, -sprinter_qty)
                self.market_order(mapped_symbol, -lagger_qty)
                
                # Set Bracket Orders (Asymmetric Short Stops & Distinct Targets)
                self.stop_market_order(mapped_symbol, (sprinter_qty + lagger_qty), current_price + self.short_stop_points)
                self.limit_order(mapped_symbol, sprinter_qty, current_price - self.sprinter_target_points)
                self.limit_order(mapped_symbol, lagger_qty, current_price - self.lagger_target_points)
                
                self.trade_entry_times[mapped_symbol] = self.time
                self.log(f"SHORT DUAL-LEG: Sprinter({sprinter_qty}) & Lagger({lagger_qty}) @ {current_price}")

        self.last_hma_val = current_hma

    def calculate_risk_adjusted_volume(self, symbol: Symbol) -> int:
        """Calculates total contract size so that a stop-loss hit equals exactly 1% of equity."""
        risk_amount_usd = self.portfolio.total_portfolio_value * 0.01
        multiplier = self.securities[symbol].symbol_properties.contract_multiplier
        # Use average of long/short stops for base volume calculation
        avg_stop = (self.long_stop_points + self.short_stop_points) / 2.0
        risk_per_contract = avg_stop * multiplier
        
        if risk_per_contract <= 0:
            return 2
            
        contracts_to_trade = int(risk_amount_usd // risk_per_contract)
        return max(2, contracts_to_trade) # Ensure at least 2 contracts for dual-leg splitting

    def liquidate_eod(self) -> None:
        """Forces all positions flat before the market close (3:45 PM EST)."""
        mapped_symbol = self._future.mapped
        if mapped_symbol and self.portfolio[mapped_symbol].invested:
            self.liquidate(mapped_symbol)
            if mapped_symbol in self.trade_entry_times:
                del self.trade_entry_times[mapped_symbol]
            self.log(f"EOD FLAT {mapped_symbol.value} @ {self.time} | Prop Firm EOD Rule Enforced")