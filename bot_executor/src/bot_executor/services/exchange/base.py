import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple


class Base(ABC):

    def __init__(self, config):
        self.exchange_name = config['exchange']
        self.config = config
        self.test_only = config["test"]
        self.target = config["target"]
        self.order_type = config["order_type"]
        self.stop_loss_type = config["stop_loss_type"]
        self.take_profit_type = config["take_profit_type"]
        self.quantity = config["quantity"]
        self.leverage = config["leverage"]
        self.sl = config.get("stop_loss")
        self.tp = config.get("take_profit")
        self.margin = config.get("margin")
        self.no_duplicate = config["duplicate"]
        self.subaccount = config.get("subaccount")
        self.options = config.get("options", {})
        self.headers = config.get("headers", {})
        self.others = config.get("others", {})
        self.positions = {}
        self.balance = None
        if self.others is None:
            self.others = {}

    def scalp_quantity(self, action: str):
        if isinstance(self.config.get("scalp_quantity"), float):

            symbol = self.make_symbol(self.config["symbol"])
            scalp_quantity = abs(self.config["scalp_quantity"])

            if scalp_quantity == 0:
                self.close_position(symbol, "SELL")
                self.close_position(symbol, "BUY")
            elif action == "BUY":
                self.close_position(symbol, "SELL")
            elif action == "SELL":
                self.close_position(symbol, "BUY")

            total_balance = self.get_balance()
            position = self.get_position(symbol, action)
            position_notional = position.get('notional', 0) if position else 0
            required_notional = scalp_quantity * total_balance * self.leverage

            if total_balance == 0:
                self.quantity = 0
            elif abs(required_notional - position_notional) <= 20:
                self.config["scalp_quantity"] = 0
            elif required_notional > position_notional + 20:
                self.close_all_orders(symbol=symbol)
                self.quantity = (required_notional - position_notional) / self.leverage
            else:
                self.close_all_orders(symbol=symbol)
                self.close_position(symbol, action)
                self.quantity = scalp_quantity * total_balance

    def clean_limit_order(self, open_order: str, symbol: str):
        result = None
        symbol = self.make_symbol(symbol)

        if open_order:
            order_info = self.exchange.fetchOrder(open_order, symbol)
            if order_info["status"] == "open":
                result = "canceled"
                self.exchange.cancelOrder(order_info.get('id'), symbol)
            else:
                result = order_info["status"]

        return result

    def validate_symbol(self, symbol: str):
        if symbol not in self.markets:
            return f"{symbol} invalid symbol"

    def validate_order(self, symbol: str, action: str):

        if self.test_only:
            return "Test only"

        err_msg = self.validate_symbol(symbol)
        if err_msg and isinstance(err_msg, str):
            return err_msg

        if self.target != "SPOT" and self.margin:
            err_msg = self.validate_margin(symbol)
            if err_msg and isinstance(err_msg, str):
                return err_msg

        if self.no_duplicate:
            err_msg = self.validate_duplicate(symbol, action)
            if err_msg and isinstance(err_msg, str):
                return err_msg

        # if config["minimum_volume"]:
        #     volume = self.get_volume(symbol)
        #     if volume is not None:
        #         if config["minimum_volume"] > volume:
        #             return True

    @abstractmethod
    def make_symbol(self, symbol: str):
        """
        different exchange has different symbol for each markets
        For exmaple,
            okx spot -> BTC/USDT
            okx future(swap) -> BTC/USDT:USDT
        """
        raise NotImplementedError

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_volume(self, symbol: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_balance(self) -> float:
        raise NotImplementedError

    def get_position(self, symbol: str, action: str):
        # return dict requires {"notional", "side", "symbol", "amount"} for position duplicate check
        if self.target == "SPOT" or self.target == "MARGIN":
            positions = self.get_all_positions()
            if symbol in positions:
                amount = positions[symbol]
                price = self.get_price(symbol)
                notional = amount * price
                side = 'BUY' if amount > 0 else "SELL"
                if side == action:
                    return {
                        'symbol': symbol,
                        'amount': amount,
                        'notional': notional,
                        'side': side,
                    }
        elif self.target == "FUTURE":
            side = {
                "BUY": {"BUY", "LONG"},
                "SELL": {"SELL", "SHORT"},
            }
            for position in self.get_all_positions():
                if position.get('symbol') == symbol and position.get('side', '').upper() in side[action]:
                    # position['side'] = action
                    return position

    def get_all_positions(self, reload=False) -> dict:
        if self.positions == {} or reload:
            if self.target != "FUTURE":
                asset = self.exchange.fetch_balance()["free"]
                self.positions = {
                    self.make_symbol(token): float(amount)
                    for token, amount in asset.items()
                }
            elif self.target == "FUTURE":
                self.positions = [i for i in self.exchange.fetchPositions() if i['notional']]
        return self.positions
      
    def close_all_positions(self):
        all_positions = set([i['symbol'] for i in self.get_all_positions()])
        for symbol in all_positions:
            self.close_position(symbol, "SELL")
            self.close_position(symbol, "BUY")
        return "closed"

    def close_all_orders(self, symbol=None) -> dict:
        for order in self.exchange.fetchOpenOrders(symbol=symbol):
            self.exchange.cancel_order(id=order["id"], symbol=order["symbol"])

    @abstractmethod
    def get_margin(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def create_market_buy(self, symbol: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_limit_buy(self, symbol: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_market_sell(self, symbol: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_limit_sell(self, symbol: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def create_oco_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float) -> Tuple[dict, dict]:
        raise NotImplementedError

    @abstractmethod
    def create_oco_short_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float) -> Tuple[dict, dict]:
        raise NotImplementedError

    @abstractmethod
    def validate_margin(self, symbol: str):
        raise NotImplementedError

    def validate_duplicate(self, symbol: str, action: str):
        logging.info(f"check {symbol} {action} {self.target} position if duplicate")
        position = self.get_position(symbol, action)
        if position:
            notional = position.get('notional', 0)

            if self.target == "FUTURE":
                if notional > (self.quantity / 20):  # if position too small then dont count as duplicate
                    logging.info(f"{symbol} has {notional} notional.")
                    return "Position duplicate"
            else:
                if action == "BUY" and notional > (self.quantity / 20):
                    logging.info(f"{symbol} has {notional} notional.")
                    return "Position duplicate"
                elif action == "SELL" and -notional > (self.quantity / 20):
                    logging.info(f"{symbol} has {notional} notional.")
                    return "Position duplicate"

    @abstractmethod
    def clean_oco_order(self, sl_order: str, tp_order: str, symbol: str):
        raise NotImplementedError

    def make_order(self, order_info: dict) -> dict:
        logging.debug("Start making order.")
        symbol = self.make_symbol(order_info["symbol"])
        action = order_info["action"]
        logging.debug(f"Symbol: {symbol}, Action: {action}")

        err_msg = self.validate_order(symbol, action)
        if err_msg and isinstance(err_msg, str):
            logging.error(err_msg)
            return err_msg

        self.scalp_quantity(action)
        if self.config.get("scalp_quantity") == 0:
            return {"msg": "close position. Ignore this error."}

        open_order = None
        entry = self.config.get("scalp_entry")
        amount = self.config.get('amount')

        if action == "BUY":
            if self.order_type == "LIMIT":
                open_order = self.create_limit_buy(symbol, amount, entry)
            elif self.order_type == "MARKET":
                open_order = self.create_market_buy(symbol, amount)
        elif action == "SELL":
            if self.order_type == "LIMIT":
                open_order = self.create_limit_sell(symbol, amount, entry)
            elif self.order_type == "MARKET":
                open_order = self.create_market_sell(symbol, amount)
        return open_order

    def make_oco_order(self, open_order: dict, order_info: dict) -> Tuple[dict, dict]:
        logging.debug("Start making OCO order.")
        sl_order = None
        tp_order = None
        symbol = self.make_symbol(order_info["symbol"])
        action = order_info["action"]
        stop_loss = order_info.get("stop_loss")
        take_profit = order_info.get("take_profit")
        tp_price = order_info.get("scalp_take_profit")
        sl_price = order_info.get("scalp_stop_loss")
        if (stop_loss or take_profit) or (tp_price or sl_price):
            if action == "BUY":
                tp_order, sl_order = self.create_oco_order(symbol, open_order, take_profit, stop_loss, tp_price, sl_price)
            elif action == "SELL":
                tp_order, sl_order = self.create_oco_short_order(symbol, open_order, take_profit, stop_loss, tp_price, sl_price)
        return tp_order, sl_order
