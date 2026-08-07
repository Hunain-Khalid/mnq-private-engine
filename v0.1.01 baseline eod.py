# region imports
from AlgorithmImports import *
# endregion

class EmaCrossoverFutureAlgorithm(QCAlgorithm):

    def initialize(self) -> None:
         # IS = 2020-01-01 to 2024-06-30
        # OOS = 2024-07-01 to 2026-06-30
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2026, 6, 30)
        self.set_cash(1000000) 
        
        self.universe_settings.asynchronous = True
        
        # Explicitly configure data consolidation to match extended market hours warning
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

        self.fast_hma = self.hma(self._future.symbol, 3, Resolution.DAILY)
        self.slow_hma = self.hma(self._future.symbol, 10, Resolution.DAILY)

        self.set_warm_up(10, Resolution.DAILY)

        # Set a fixed stop-loss point value for the 1% risk model (e.g., 50 S&P points)
        self.stop_loss_points = 50.0

        self.schedule.on(
            self.date_rules.every_day(self._future.symbol),
            self.time_rules.after_market_open(self._future.symbol, 30),
            self.check_signals_and_trade,

            self.date_rules.every_day(self._future.symbol),
            self.time_rules.before_market_close(self._future.symbol, 15), # 15 minutes before close (3:45 PM EST)
            self.liquidate_eod
        )

    def on_data(self, slice: Slice) -> None:
        pass

    def check_signals_and_trade(self) -> None:
        if self.is_warming_up or not self.fast_hma.is_ready or not self.slow_hma.is_ready:
            return

        mapped_symbol = self._future.mapped
        if mapped_symbol is None:
            return

        if not self.securities[mapped_symbol].exchange.exchange_open:
            return

        fast_val = self.fast_hma.current.value
        slow_val = self.slow_hma.current.value
        current_quantity = self.portfolio[mapped_symbol].quantity

        # Calculate exact contract size for 1% portfolio risk
        target_quantity = self.calculate_risk_adjusted_volume(mapped_symbol)

        # Execution Logic
        if fast_val > slow_val:
            # If we are not already long at the correct size
            if current_quantity <= 0:
                # Use market_order instead of set_holdings to manually enforce precise sizes
                self.liquidate(mapped_symbol)
                self.market_order(mapped_symbol, target_quantity)
                self.log(f"BUY {target_quantity} {mapped_symbol.value} @ {self.time} | 1% Risk Size")

        elif fast_val < slow_val:
            # If we are not already short at the correct size
            if current_quantity >= 0:
                self.liquidate(mapped_symbol)
                self.market_order(mapped_symbol, -target_quantity)
                self.log(f"SHORT -{target_quantity} {mapped_symbol.value} @ {self.time} | 1% Risk Size")

    def calculate_risk_adjusted_volume(self, symbol: Symbol) -> int:
        """Calculates contract size so that a stop-loss hit equals exactly 1% of equity."""
        # 1. Get 1% of total portfolio value
        risk_amount_usd = self.portfolio.total_portfolio_value * 0.01
        
        # 2. Get the contract multiplier (For ES, this is $50 per full index point)
        multiplier = self.securities[symbol].symbol_properties.contract_multiplier
        
        # 3. Calculate risk per single contract based on your stop-loss distance
        risk_per_contract = self.stop_loss_points * multiplier
        
        if risk_per_contract <= 0:
            return 1
            
        # 4. Total contracts to trade (rounded down to a whole number)
        contracts_to_trade = int(risk_amount_usd // risk_per_contract)
        
        # Ensure we always trade at least 1 contract if cash permits
        return max(1, contracts_to_trade)

def liquidate_eod(self) -> None:
        """Forces all positions flat before the market close to eliminate overnight risk."""
        mapped_symbol = self._future.mapped
        if mapped_symbol and self.portfolio[mapped_symbol].invested:
            self.liquidate(mapped_symbol)
            self.log(f"EOD FLAT {mapped_symbol.value} @ {self.time} | Eliminating Overnight Risk")