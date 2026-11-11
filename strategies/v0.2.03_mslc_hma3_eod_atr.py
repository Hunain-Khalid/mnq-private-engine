# region imports
from AlgorithmImports import *
# endregion

class SingleHMASlopeFutureAlgorithm(QCAlgorithm):

    def initialize(self) -> None:
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

        # 3. Friction & Risk Parameters (WSC Friction Floor = $12)
        self.worst_case_friction_usd = 12.0
        self.stop_loss_points = 40.0

        # 4. Sprinter vs Lagger Parameters
        # ES Contract Multiplier is $50 per point. 
        # To clear $12 friction + desired net profit, calculate points dynamically or set fixed points:
        # e.g., 1.5 points on ES = $75 gross -> minus $12 friction = ~$63 clean win.
        self.sprinter_target_points = 2.0  # 2 points on ES = $100 gross (> $12 WSC friction)
        self.atr_trailing_multiplier = 2.5 # Lagger trails by 2.5 x ATR

        self.last_hma_val = 0.0
        self.lagger_trailing_stops = {} # Tracks dynamic trailing stops for lagger leg

        # 5. Fixed Entry Timing: 9:31 AM EST (Capturing Opening Range)
        self.schedule.on(
            self.date_rules.every_day(self._future.symbol),
            self.time_rules.after_market_open(self._future.symbol, 1), # 9:31 AM EST
            self.check_signals_and_trade
        )

        self.schedule.on(
            self.date_rules.every_day(self._future.symbol),
            self.time_rules.before_market_close(self._future.symbol, 15), # 3:45 PM EST EOD Rule
            self.liquidate_eod
        )

    def on_data(self, slice: Slice) -> None:
        # Continuous ATR Trailing Stop management for the Lagger leg
        mapped_symbol = self._future.mapped
        if not mapped_symbol or not self.portfolio[mapped_symbol].invested:
            return

        current_price = self.securities[mapped_symbol].price
        current_atr = self.atr_indicator.current.value
        current_quantity = self.portfolio[mapped_symbol].quantity

        if mapped_symbol in self.lagger_trailing_stops:
            stop_data = self.lagger_trailing_stops[mapped_symbol]
            direction = stop_data['direction']
            best_price = stop_data['best_price']

            if direction == "LONG":
                # Update high watermark price
                if current_price > best_price:
                    self.lagger_trailing_stops[mapped_symbol]['best_price'] = current_price
                    best_price = current_price
                
                # Calculate new trailing stop based on ATR
                new_stop = best_price - (current_atr * self.atr_trailing_multiplier)
                if new_stop > stop_data['current_stop']:
                    self.lagger_trailing_stops[mapped_symbol]['current_stop'] = new_stop
                    
                # If price breaches trailing stop, flatten
                if current_price <= self.lagger_trailing_stops[mapped_symbol]['current_stop']:
                    self.liquidate(mapped_symbol)
                    self.log(f"ATR TRAILING STOP HIT (LONG) @ {current_price}")
                    del self.lagger_trailing_stops[mapped_symbol]

            elif direction == "SHORT":
                # Update low watermark price
                if current_price < best_price:
                    self.lagger_trailing_stops[mapped_symbol]['best_price'] = current_price
                    best_price = current_price
                
                # Calculate new trailing stop based on ATR
                new_stop = best_price + (current_atr * self.atr_trailing_multiplier)
                if new_stop < stop_data['current_stop']:
                    self.lagger_trailing_stops[mapped_symbol]['current_stop'] = new_stop
                    
                # If price breaches trailing stop, flatten
                if current_price >= self.lagger_trailing_stops[mapped_symbol]['current_stop']:
                    self.liquidate(mapped_symbol)
                    self.log(f"ATR TRAILING STOP HIT (SHORT) @ {current_price}")
                    del self.lagger_trailing_stops[mapped_symbol]

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

        hma_slope_positive = current_hma > self.last_hma_val
        hma_slope_negative = current_hma < self.last_hma_val
        volatility_confirmed = current_atr > 0

        # Calculate exact risk volume (Multiples of 2 for clean 50/50 Sprinter/Lagger split)
        total_target_qty = self.calculate_risk_adjusted_volume(mapped_symbol)
        sprinter_qty = max(1, total_target_qty // 2)
        lagger_qty = max(1, total_target_qty - sprinter_qty)

        # Execution Logic: 9:31 AM Open
        if hma_slope_positive and volatility_confirmed:
            if current_quantity <= 0:
                self.liquidate(mapped_symbol)
                
                # Enter Dual Legs
                self.market_order(mapped_symbol, sprinter_qty)
                self.market_order(mapped_symbol, lagger_qty)
                
                # Sprinter Target (WSC Friction-Guaranteed Profit Lock)
                self.limit_order(mapped_symbol, -sprinter_qty, current_price + self.sprinter_target_points)
                
                # Initialize ATR Trailing Stop for Lagger
                initial_stop = current_price - (current_atr * self.atr_trailing_multiplier)
                self.lagger_trailing_stops[mapped_symbol] = {
                    'direction': 'LONG',
                    'best_price': current_price,
                    'current_stop': initial_stop
                }
                
                self.log(f"BUY 9:31 OPEN | Sprinter({sprinter_qty}) @ +{self.sprinter_target_points}pts | Lagger({lagger_qty}) ATR Trail")

        elif hma_slope_negative and volatility_confirmed:
            if current_quantity >= 0:
                self.liquidate(mapped_symbol)
                
                # Enter Dual Legs
                self.market_order(mapped_symbol, -sprinter_qty)
                self.market_order(mapped_symbol, -lagger_qty)
                
                # Sprinter Target (WSC Friction-Guaranteed Profit Lock)
                self.limit_order(mapped_symbol, sprinter_qty, current_price - self.sprinter_target_points)
                
                # Initialize ATR Trailing Stop for Lagger
                initial_stop = current_price + (current_atr * self.atr_trailing_multiplier)
                self.lagger_trailing_stops[mapped_symbol] = {
                    'direction': 'SHORT',
                    'best_price': current_price,
                    'current_stop': initial_stop
                }
                
                self.log(f"SHORT 9:31 OPEN | Sprinter({sprinter_qty}) @ -{self.sprinter_target_points}pts | Lagger({lagger_qty}) ATR Trail")

        self.last_hma_val = current_hma

    def calculate_risk_adjusted_volume(self, symbol: Symbol) -> int:
        """Ensures volume is a multiple of 2 for clean 50/50 leg splitting."""
        risk_amount_usd = self.portfolio.total_portfolio_value * 0.01
        multiplier = self.securities[symbol].symbol_properties.contract_multiplier
        risk_per_contract = self.stop_loss_points * multiplier
        
        if risk_per_contract <= 0:
            return 2
            
        contracts = int(risk_amount_usd // risk_per_contract)
        contracts = max(2, contracts)
        # Force even multiple of 2
        if contracts % 2 != 0:
            contracts += 1
        return contracts

    def liquidate_eod(self) -> None:
        """Forces all positions flat before the market close (3:45 PM EST)."""
        mapped_symbol = self._future.mapped
        if mapped_symbol and self.portfolio[mapped_symbol].invested:
            self.liquidate(mapped_symbol)
            if mapped_symbol in self.lagger_trailing_stops:
                del self.lagger_trailing_stops[mapped_symbol]
            self.log(f"EOD FLAT {mapped_symbol.value} @ {self.time} | Prop Firm EOD Rule Enforced")