import ccxt
import json
import logging
from typing import List, Dict, Tuple


class FTXClient():

    def __init__(self, config: dict):
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
        self.no_duplicate = not config["duplicate"]
        self.subaccount = config.get("subaccount")

        options = {
            "adjustForTimeDifference": True,
            "verbose": True
        }
        headers = {}
        if self.subaccount:
            headers = {
                'FTX-SUBACCOUNT': self.subaccount
            }
            logging.info(f"headers: {headers}")
        self.exchange = getattr(ccxt, config["exchange_setting"]["exchange"])({
            "enableRateLimit": True,
            "apiKey": config["api_key"],
            "secret": config["api_secret"],
            'options': options,
            'headers': headers,
        })

        try:
            self.exchange.check_required_credentials()
        except Exception as e:
            logging.info(f"Authenticate Requirements: {json.dumps(self.exchange.requiredCredentials, indent=4)}")
            raise e

        self.markets = self.exchange.loadMarkets(True)

    def get_volume(self, symbol: str) -> float:
        try:
            self.exchange.loadMarkets(True)
            symbol = symbol.replace("USDT", "USD")
            market = self.exchange.markets[symbol]
            info = market["info"]
            return float(info["volumeUsd24h"])
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")

    def get_price(self, symbol: str) -> float:
        self.exchange.loadMarkets(True)
        symbol = symbol.replace("USDT", "USD")
        return float(self.exchange.fetchTicker(symbol)['bid'])

    def get_balance(self):
        balance = 0
        info = self.exchange.fetch_balance()["info"]
        for coin in info["reuslt"]:
            if coin['coin'] == "USD":
                balance = coin["availableWithoutBorrow"]
        return float(balance)

    def get_margin(self, symbol: str) -> float:
        self.exchange.loadMarkets(True)
        margin = self.exchange.private_get_account()["result"]["marginFraction"]
        return 999 if margin is None else float(margin)

    def create_market_buy(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        logging.info(f"""
            Market Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createMarketBuyOrder(symbol, amount)
        logging.info(f"Open average price : {order['average']}")
        return order

    def create_limit_buy(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        logging.info(f"""
            Limit Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createLimitBuyOrder(symbol, amount, price)
        order["average"] = order.get("price", price)
        return order

    def create_market_sell(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        logging.info(f"""
            Market Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createMarketSellOrder(symbol, amount)
        logging.info(f"Sell average price : {order['average']}")
        return order

    def create_limit_sell(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        logging.info(f"""
            Limit Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createLimitSellOrder(symbol, amount, price)
        order["average"] = order.get("price", price)
        return order

    def create_oco_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float):
        open_order = self.exchange.fetchOrder(open_order["id"])
        amount = float(open_order["amount"])
        price = float(open_order["average"]) if open_order.get("average") else float(open_order["price"])
        tp_price = price * (1 + take_profit)
        sl_price = price * (1 - stop_loss)
        tp_order = None
        sl_order = None
        logging.info(f"""
            Create OCO order
            Amount: {amount},
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)

        params = {
            "market": symbol,
            "side": "sell",
            "triggerPrice": tp_price,
            "size": amount,
            "type": "takeProfit",
            "reduceOnly": True
        }
        if self.take_profit_type == "LIMIT":
            params["orderPrice"] = tp_price
        tp_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        params = {
            "market": symbol,
            "side": "sell",
            "triggerPrice": sl_price,
            "size": amount,
            "type": "stop",
            "reduceOnly": True
        }
        if self.stop_loss_type == "LIMIT":
            params["orderPrice"] = sl_price
        sl_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        return tp_order, sl_order

    def create_oco_short_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float):
        open_order = self.exchange.fetchOrder(open_order["id"])
        amount = float(open_order["amount"])
        price = float(open_order["average"]) if open_order.get("average") else float(open_order["price"])
        tp_price = price * (1 - take_profit)
        sl_price = price * (1 + stop_loss)
        tp_order = None
        sl_order = None
        logging.info(f"""
            Create OCO short order
            Amount: {amount},
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)

        params = {
            "market": symbol,
            "side": "buy",
            "triggerPrice": tp_price,
            "size": amount,
            "type": "takeProfit",
            "reduceOnly": True
        }
        if self.take_profit_type == "LIMIT":
            params["orderPrice"] = tp_price
        tp_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        params = {
            "market": symbol,
            "side": "buy",
            "triggerPrice": sl_price,
            "size": amount,
            "type": "stop",
            "reduceOnly": True
        }
        if self.stop_loss_type == "LIMIT":
            params["orderPrice"] = sl_price
        sl_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        return tp_order, sl_order

    def process_oco_order(self, oco_order):
        tp_order = None
        sl_order = None
        for order in oco_order["orderReports"]:
            if "STOP_LOSS" in order["type"].upper():
                sl_order = order
            else:
                tp_order = order
        return tp_order, sl_order

    def validate_symbol(self, symbol: str):
        self.markets = self.exchange.loadMarkets(True)
        if symbol not in self.markets:
            error_msg = f"{symbol} invalid symbol"
            logging.error(error_msg)
            raise Exception(error_msg)

    def validate_action(self, action: str):
        if action not in ["BUY", "SELL"]:
            error_msg = f"invalid action [{action}]"
            logging.error(error_msg)
            raise Exception(logging.error(error_msg))

    def validate_margin(self, symbol: str):
        margin = self.get_margin(symbol)
        logging.info(f"Current margin: {margin}, minimum margin: {self.margin}.")
        error_msg = "invalid margin"
        if margin < self.margin:
            logging.error(error_msg)
            raise Exception(error_msg)

    def validate_duplicate(self, symbol: str):
        if self.target == "SPOT" or self.target == "MARGIN":
            logging.info("check spot duplicate")
            token = symbol.split('/')[0]
            asset = self.exchange.fetch_balance()["total"]
            amount = float(asset.get(token, 0))
            price = self.get_price(symbol)
            notional = amount * price
            if notional > 1:
                logging.info(f"{symbol} has {notional} notional.")
                raise Exception("Position duplicate")
        elif self.target == "FUTURE":
            logging.info("check future duplicate")
            positions = self.exchange.fetchPositions()
            for position in positions:
                if "symbol" in position:
                    position = position.get("info", {})
                if position.get('future') == symbol and position.get('entryPrice') and position.get('side'):
                    side = position['side']
                    logging.info(f"{symbol} has {side} position.")
                    raise Exception("Position duplicate")

        return False

    def validate_order(self, symbol: str, action: str):

        if self.test_only:
            logging.error("Test only")
            raise Exception("Test only")

        self.validate_symbol(symbol)
        self.validate_action(action)

        if self.target != "SPOT":
            self.validate_margin(symbol)

        if action == "sell" and self.target != "FUTURE":
            logging.error("short only in future")
            raise Exception("short only in future")

        if self.no_duplicate:
            self.validate_duplicate(symbol)

        # if config["minimum_volume"]:
        #     volume = self.get_volume(symbol)
        #     if volume is not None:
        #         if config["minimum_volume"] > volume:
        #             return True

    def make_order(self, order_info: dict):
        logging.info("Start making order.")
        symbol = order_info["symbol"]
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

    def make_oco_order(self, open_order: dict, order_info: dict):
        sl_order = None
        tp_order = None
        symbol = order_info["symbol"]
        action = order_info["action"]
        stop_loss = order_info.get("stop_loss")
        take_profit = order_info.get("take_profit")
        if stop_loss and take_profit:
            if action == "BUY":
                tp_order, sl_order = self.create_oco_order(symbol, open_order, take_profit, stop_loss)
            elif action == "SELL":
                tp_order, sl_order = self.create_oco_short_order(symbol, open_order, take_profit, stop_loss)
        return tp_order, sl_order
