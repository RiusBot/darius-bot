from abc import ABC, abstractmethod
from typing import List, Dict, Tuple


class Base(ABC):

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
            error_msg = f"{symbol} invalid symbol"
            logging.error(error_msg)
            raise Exception(error_msg)

    def validate_order(self, symbol: str, action: str):

        if self.test_only:
            logging.error("Test only")
            raise Exception("Test only")

        self.validate_symbol(symbol)

        if self.target != "SPOT" and self.margin:
            self.validate_margin(symbol)

        if action == "sell" and self.target != "FUTURE":
            logging.error("short only in future")
            raise Exception("short only in future")

        if self.no_duplicate:
            self.validate_duplicate(symbol, action)

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
        
    @abstractmethod
    def get_position(self, symbol: str) -> dict:
        # return dict requires {"notional", "side"} for position duplicate check
        raise NotImplementedError

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
        position = self.get_position(symbol)
        notional = position['notional']

        if self.target == "FUTURE":
            side = position.get('side')
            logging.info(f"{symbol} has exists {side} position.")
            side_map = {
                "BUY": ("BUY", "LONG"),
                "SELL": ("SHORT", "SELL")
            }
            if side.upper() not in side_map[action]:
                return  # opposite side then dont count as duplicate

        if notional > (self.quantity / 20):  # if position too small then dont count as duplicate
            logging.info(f"{symbol} has {notional} notional.")
            raise Exception("Position duplicate")

    @abstractmethod
    def clean_oco_order(self, sl_order: str, tp_order: str, symbol: str):
        raise NotImplementedError

    def make_order(self, order_info: dict) -> dict:
        logging.info("Start making order.")
        symbol = self.make_symbol(order_info["symbol"])
        action = order_info["action"]
        logging.info(f"Symbol: {symbol}, Action: {action}")
        self.validate_order(symbol, action)

        open_order = None
        if action == "BUY":
            if self.order_type == "LIMIT":
                open_order = self.create_limit_buy(symbol)
            elif self.order_type == "MARKET":
                open_order = self.create_market_buy(symbol)
        elif action == "SELL":
            if self.order_type == "LIMIT":
                open_order = self.create_limit_sell(symbol)
            elif self.order_type == "MARKET":
                open_order = self.create_market_sell(symbol)
        return open_order

    def make_oco_order(self, open_order: dict, order_info: dict) -> Tuple[dict, dict]:
        logging.info("Start making OCO order.")
        sl_order = None
        tp_order = None
        symbol = self.make_symbol(order_info["symbol"])
        action = order_info["action"]
        stop_loss = order_info.get("stop_loss")
        take_profit = order_info.get("take_profit")
        tp_price = order_info.get("scalp_take_profit")
        sl_price = order_info.get("scalp_stop_loss")
        if (stop_loss and take_profit) or (tp_price and sl_price):
            if action == "BUY":
                tp_order, sl_order = self.create_oco_order(symbol, open_order, take_profit, stop_loss, tp_price, sl_price)
            elif action == "SELL":
                tp_order, sl_order = self.create_oco_short_order(symbol, open_order, take_profit, stop_loss, tp_price, sl_price)
        return tp_order, sl_order
