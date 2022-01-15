import ccxt
import json
import logging
from typing import List, Dict, Tuple


class BinanceClient():

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
        self.no_duplicate = config["duplicate"]

        options = {
            "defaultType": self.target.lower(),
            "adjustForTimeDifference": True,
            "verbose": True
        }
        headers = {}
        self.exchange = ccxt.binance({
            "enableRateLimit": True,
            "apiKey": config["api_key"],
            "secret": config["api_secret"],
            'options': options,
            'headers': headers
        })

        try:
            self.exchange.check_required_credentials()
        except Exception as e:
            logging.error(f"Authenticate Requirements: {json.dumps(self.exchange.requiredCredentials, indent=4)}")
            raise e

        self.markets = self.exchange.loadMarkets(True)
    
    def get_position_param(self, side: str):
        if self.target == "FUTURE":
            return {"positionSide": self.get_position_side(side)}
        else:
            return {}
    
    def get_position_mode(self):
        # true: hedge, false: one-way
        return self.exchange.fapiPrivate_get_positionside_dual().get('dualSidePosition')
    
    def get_position_side(self, side: str):
        if self.get_position_mode():
            if side == "BUY":
                return "LONG"
            else:
                return "SHORT"
        else:
            return "BOTH"
    
    def make_symbol(self, symbol: str):
        return f"{symbol}/USDT"
    
    def get_volume(self, symbol: str) -> float:
        try:
            symbol = symbol.replace("/", "")
            return float(self.exchange.fapiPublic_get_ticker_24hr({'symbol': symbol})["volume"])
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")

    def get_price(self, symbol: str) -> float:
        symbol = symbol.replace("/", "")
        return float(self.exchange.fetchTicker(symbol)['info']["lastPrice"]) * 1.01

    def get_balance(self):
        balance = 0
        if self.target == "SPOT":
            assets = self.exchange.fetch_balance()["info"]["balances"]
            for asset in assets:
                if asset["asset"] == "USDT":
                    balance = asset["free"]
        elif self.target == "MARGIN":
            assets = self.exchange.fetch_balance()["info"]["userAssets"]
            for asset in assets:
                if asset["asset"] == "USDT":
                    balance = asset["free"]
        elif self.target == "FUTURE":
            balance = self.exchange.fetch_balance()["info"]['availableBalance']
        logging.info(f"Balance remain: {balance}")
        return float(balance)

    def get_margin(self, symbol: str) -> float:
        margin = None
        if self.target == "SPOT":
            margin = 999
        elif self.target == "MARGIN":
            info = self.exchange.fetch_balance()["info"]
            margin = 999 if info["marginLevel"] is None else float(info["marginLevel"])
        elif self.target == "FUTURE":
            info = self.exchange.fetch_balance()
            maintenance_margin = float(info["info"]["totalMaintMargin"])
            margin_balance = float(info["info"]["totalMarginBalance"])
            if margin_balance == 0:
                marginRatio = 0
            else:
                marginRatio = maintenance_margin / margin_balance
            margin = marginRatio

        logging.info(f"Margin level/ratio: {margin}")
        return margin

    def create_market_buy(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        logging.info(f"""
            Market Buy {symbol}
            price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createMarketBuyOrder(symbol, amount, params=self.get_position_param("BUY"))
        logging.info(f"Open average price : {order['average']}")
        return order

    def create_limit_buy(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        logging.info(f"""
            Limit Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        params = self.get_position_param("BUY")
        params["timeInForce"] = "IOC"
        order = self.exchange.createLimitBuyOrder(symbol, amount, price, params=params)
        order["average"] = float(order.get("price", price))
        order["amount"] = float(order.get("filled", 0))
        return order

    def create_market_sell(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        logging.info(f"""
            Market Sell {symbol}
            Amount : {amount}
            Price: {price}
        """)
        order = self.exchange.createMarketSellOrder(symbol, amount, params=self.get_position_param("SELL"))
        logging.info(f"Sell average price : {order['average']}")
        return order

    def create_limit_sell(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        logging.info(f"""
            Limit Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        params = self.get_position_param("SELL")
        params["timeInForce"] = "IOC"
        order = self.exchange.createLimitSellOrder(symbol, amount, price, params=params)
        order["average"] = float(order.get("price", price))
        order["amount"] = float(order.get("filled", 0))
        return order

    def create_oco_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        amount = float(open_order["amount"]) * 0.99
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        price = float(open_order["average"]) if open_order.get("average") else float(open_order["price"])
        if tp_price is None:
            tp_price = price * (1 + take_profit)
        if sl_price is None:
            sl_price = price * (1 - stop_loss)

        sl_price = max(sl_price, price * 0.01)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))

        tp_order = None
        sl_order = None
        logging.info(f"""
            Create OCO order
            Amount: {amount}
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        
        if amount <= 0:
            return tp_order, sl_order

        if self.target == "FUTURE":
            tp_order_type = {
                "MARKET": "TAKE_PROFIT_MARKET",
                "LIMIT": "TAKE_PROFIT",
                "TRAILING": "TRAILING_STOP_MARKET"
            }.get(self.take_profit_type)
            sl_order_type = {
                "MARKET": "STOP_MARKET",
                "LIMIT": "STOP",
                "TRAILING": "TRAILING_STOP_MARKET"
            }.get(self.stop_loss_type)

            if self.take_profit_type != "TRAILING":
                tp_params = {
                    "stopPrice": tp_price,
                    "closePosition": (tp_order_type=="TAKE_PROFIT_MARKET"),
                    "priceProtect": True,
                    "positionSide": self.get_position_side("SHORT")
                }
            else:
                tp_params = {
                    "callbackRate": take_profit * 100,
                    "priceProtect": True,
                    "positionSide": self.get_position_side("SHORT")
                }
                if not self.get_position_mode():
                    tp_params["reduceOnly"] = True

            tp_order = self.exchange.create_order(
                symbol,
                type=tp_order_type,
                side="SELL",
                price=tp_price,
                amount=amount,
                params=tp_params
            )

            if self.stop_loss_type != "TRAILING":
                sl_params = {
                    "stopPrice": sl_price,
                    "closePosition": (sl_order_type=="STOP_MARKET"),
                    "priceProtect": True,
                    "positionSide": self.get_position_side("SHORT")
                }
            else:
                sl_params = {
                    "callbackRate": stop_loss * 100,
                    "priceProtect": True,
                    "positionSide": self.get_position_side("SHORT")
                }
                if not self.get_position_mode():
                    sl_params["reduceOnly"] = True

            sl_order = self.exchange.create_order(
                symbol,
                type=sl_order_type,
                side="SELL",
                amount=amount,
                price=sl_price,
                params=sl_params
            )
        elif self.target == "SPOT":
            tp_order_type = "TAKE_PROFIT_LIMIT" if self.take_profit_type == "LIMIT" else "TAKE_PROFIT"
            sl_order_type = "STOP_LOSS_LIMIT" if self.stop_loss_type == "LIMIT" else "STOP_LOSS"
            oco_order = self.exchange.private_post_order_oco({
                "symbol": symbol.replace("/", ""),
                "side": "SELL",
                "quantity": amount,
                "price": tp_price,
                "stopPrice": sl_price,
                "stopLimitPrice": sl_price,
                "stopLimitTimeInForce": "GTC"
            })
            tp_order, sl_order = self.process_oco_order(oco_order)
        elif self.target == "MARGIN":
            oco_order = self.exchange.sapi_post_margin_order_oco({
                "symbol": symbol,
                "side": "SELL",
                "quantity": amount,
                "price": tp_price,
                "stopPrice": sl_price,
                "stopLimitPrice": sl_price,
                "stopLimitTimeInForce": "GTC"
            })
            tp_order, sl_order = self.process_oco_order(oco_order)
        return tp_order, sl_order

    def create_oco_short_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        amount = float(open_order["amount"]) * 0.99
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        price = float(open_order["average"]) if open_order.get("average") else float(open_order["price"])
        if tp_price is None:
            tp_price = price * (1 - take_profit)
        if sl_price is None:
            sl_price = price * (1 + stop_loss)

        tp_price = max(price * 0.01, tp_price)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))

        tp_order = None
        sl_order = None
        tp_order_type = {
            "MARKET": "TAKE_PROFIT_MARKET",
            "LIMIT": "TAKE_PROFIT",
            "TRAILING": "TRAILING_STOP_MARKET"
        }.get(self.take_profit_type)
        sl_order_type = {
            "MARKET": "STOP_MARKET",
            "LIMIT": "STOP",
            "TRAILING": "TRAILING_STOP_MARKET"
        }.get(self.stop_loss_type)

        logging.info(f"""
            Create OCO short order
            Amount: {amount},
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        
        if amount <= 0:
            return tp_order, sl_order

        if self.target == "FUTURE":

            if self.take_profit_type != "TRAILING":
                tp_params = {
                    "stopPrice": tp_price,
                    "closePosition": (tp_order_type=="TAKE_PROFIT_MARKET"),
                    "priceProtect": True,
                    "positionSide": self.get_position_side("BUY")
                }
            else:
                tp_params = {
                    "callbackRate": take_profit * 100,
                    "priceProtect": True,
                    "positionSide": self.get_position_side("BUY")
                }
                if not self.get_position_mode():
                    tp_params["reduceOnly"] = True

            tp_order = self.exchange.create_order(
                symbol,
                type=tp_order_type,
                side="BUY",
                price=tp_price,
                amount=amount,
                params=tp_params
            )

            if self.stop_loss_type != "TRAILING":
                sl_params = {
                    "stopPrice": sl_price,
                    "closePosition": (sl_order_type=="STOP_MARKET"),
                    "priceProtect": True,
                    "positionSide": self.get_position_side("BUY")
                }
            else:
                sl_params = {
                    "callbackRate": stop_loss * 100,
                    "priceProtect": True,
                    "positionSide": self.get_position_side("BUY")
                }
                if not self.get_position_mode():
                    sl_params["reduceOnly"] = True

            sl_order = self.exchange.create_order(
                symbol,
                type=sl_order_type,
                side="BUY",
                price=sl_price,
                amount=amount,
                params=sl_params
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
        if self.target == "FUTURE":
            if margin > self.margin:
                logging.error(error_msg)
                raise Exception(error_msg)
        elif self.target == "MARGIN":
            if margin < self.margin:
                logging.error(error_msg)
                raise Exception(error_msg)

    def validate_duplicate(self, symbol: str, action: str):
        if self.target == "SPOT" or self.target == "MARGIN":
            logging.info("check spot duplicate")
            token = symbol.split('/')[0]
            asset = self.exchange.fetch_balance()["total"]
            amount = float(asset.get(token, 0))
            price = self.get_price(symbol)
            notional = amount * price
            if notional > 10:
                logging.info(f"{symbol} has {notional} notional.")
                raise Exception("Position duplicate")
        elif self.target == "FUTURE":
            logging.info("check future duplicate")
            positions = self.exchange.fetchPositions()
            for position in positions:
                if position.get('symbol') == symbol and position.get('side'):
                    side = position.get('side')
                    logging.info(f"{symbol} has {side} position.")
                    side_map = {
                        "BUY": ("BUY", "LONG"),
                        "SELL": ("SHORT", "SELL")
                    }
                    if side.upper() in side_map[action]:
                        raise Exception("Position duplicate")

    def validate_order(self, symbol: str, action: str):

        if self.test_only:
            logging.error("Test only")
            raise Exception("Test only")

        self.validate_symbol(symbol)
        self.validate_action(action)

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

    def make_order(self, order_info: dict):
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

    def make_oco_order(self, open_order: dict, order_info: dict):
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
