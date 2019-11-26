from margin_strategy_sdk import *

##################################################################
# User settings:
##################################################################
BUY_PRICE = 0.0207
SELL_PRICE = 0.0212
AMOUNT = 0.1
START_ON_BUY = True


class Strategy(StrategyBase):
    ##############################################################
    # strategy logic methods
    ##############################################################
    def __init__(self):
        super(Strategy, self).__init__()
        self.waiting_order_id = 0
        self.current_order = None

    def init(self) -> None:
        tcm = self.get_trading_capability_manager()
        buy_total = tcm.get_due_buy_total(AMOUNT, BUY_PRICE)
        sell_total = tcm.get_sell_total_to_receive(AMOUNT, SELL_PRICE)
        effective_gain = round(sell_total-buy_total, 8)
        eff_gain_percentage = round(effective_gain/buy_total*100, 3)
        # If we do not ensure this, the bot can get into a rapid buy-sell-cycle.
        assert(BUY_PRICE < SELL_PRICE)
        print("Strategy is going to be run with an expected effective gain of approx. {} {} ({}%) per buy-sell-cycle."
              .format(effective_gain, self.get_second_currency(), eff_gain_percentage))

    def get_strategy_config(self) -> StrategyConfig:
        s = StrategyConfig()
        s.required_data_updates = set()
        s.normalize_exchange_buy_amounts = True
        return s

    def save_strategy_state(self) -> Dict[str, str]:
        if self.current_order is None:
            return {}
        return {"current_order_id": str(self.current_order.id)}

    def restore_strategy_state(self, strategy_state: Dict[str, str]) -> None:
        if "current_order_id" in strategy_state:
            open_orders = self.get_buffered_open_orders()
            for order in open_orders:
                if order.id == int(strategy_state["current_order_id"]):
                    self.current_order = order

    def place_order(self, buy_side: bool, amount: float = AMOUNT):
        tcm = self.get_trading_capability_manager()
        amount = amount
        price = BUY_PRICE if buy_side else SELL_PRICE
        print("placing {} order".format("buy" if buy_side else "sell"))
        amount = tcm.round_amount(amount, RoundingType.ROUND)
        assert(tcm.is_limit_order_valid(buy_side, amount, price))
        self.waiting_order_id = self.place_limit_order(buy_side, amount, price)

    def start(self) -> None:
        self.place_order(START_ON_BUY)

    def stop(self) -> None:
        # nothing to do here for now.
        pass

    def suspend(self) -> None:
        # nothing to do here for now.
        pass

    def unsuspend(self) -> None:
        # nothing to do here for now.
        pass

    ##############################################################
    # private update methods
    ##############################################################
    def on_order_update(self, update: OrderUpdate) -> None:
        print("Order update status was: ", update.status)
        if update.status == OrderUpdate.FILLED or update.status == OrderUpdate.ADAPTED_AND_FILLED:
            # Place an order on the opposite side
            self.place_order(not self.current_order.buy)
            self.current_order = None
        elif update.status == OrderUpdate.ADAPTED or \
                update.status == OrderUpdate.PARTIALLY_FILLED or \
                update.status == OrderUpdate.OTHER_CHANGE:
            # Update the order
            self.current_order = update.updated_order
        elif update.status == OrderUpdate.NO_CHANGE:
            # Here we do nothing
            pass
        elif update.status == OrderUpdate.REAPPEARED:
            # We will handle this later
            pass
        elif update.status == OrderUpdate.DISAPPEARED:
            # We will handle this later
            pass
        elif update.status == OrderUpdate.CANCELED:
            # Replace the order (remaining_amount becomes new amount)
            self.place_order(self.current_order.buy, self.current_order.remaining_amount)
            self.current_order = None

    def on_place_order_success(self, place_order_id: int, order: Order) -> None:
        if self.waiting_order_id == place_order_id:
            if order.remaining_amount == 0.0:
                self.place_order(not order.buy)
            else:
                self.current_order = order
                self.waiting_order_id = None
        else:
            print("Did not have waiting order id for {}".format(place_order_id))
            write_log(LogLevel.WARNING, "Did not have waiting order id for {}".format(place_order_id))

    def on_place_order_error_string(self: StrategyBase, place_order_id: int, error: str) -> None:
        self.exit(ExitReason.ERROR, error)

    def on_cancel_order_success(self: StrategyBase, order_id: int, canceled_order: Order):
        self.exit(ExitReason.ERROR, "strategy is not supposed cancel an order")

    def on_cancel_order_error_string(self: StrategyBase, order_id: int, error: str) -> None:
        self.exit(ExitReason.ERROR, error)
