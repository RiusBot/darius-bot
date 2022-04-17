import ccxt
import json
import logging
from typing import List, Dict, Tuple

from .base import Base


class BybitClient(Base):

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
        self.use_all_collateral = config["use_all_collateral"]

        options = {
            "defaultType": self.target.lower(),
            "adjustForTimeDifference": True,
            "verbose": True
        }
        headers = {}
        self.exchange = ccxt.bybit({
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
    
    def get_position_param(self,symbol: str, side: str, tp_price: float, sl_price: float):
        if self.target == "FUTURE":
            return {"positionSide": self.get_position_side(symbol, side), 'position_idx': 0, 'take_profit': tp_price, 'stop_loss': sl_price}
        else:
            return {}
                
    def get_position_mode(self, symbol: str):
        # BothSide: hedge, MergedSingle: one-way
        symbol = symbol.replace("/", "")
        position = [position for position in self.exchange.private_linear_get_position_list().get('result') if position.get('data').get('symbol') == symbol][0]
        if position.get('data').get('symbol') == symbol:
            return position.get('data').get('mode')
    
    def get_position_side(self, symbol: str, side: str):
        if self.get_position_mode(symbol) == 'MergedSingle':
            if side == "Buy":
                return "Buy"
            else:
                return "Sell"
        else:
            return "BOTH"
        
    def make_symbol(self, symbol: str):
        return f"{symbol}/USDT"
    
    def get_volume(self, symbol: str) -> float:
        try:
            symbol = symbol.replace("/", "")
            return float(self.exchange.fetch_ticker(symbol)['info']['volume_24h'])            
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")

    def get_price(self, symbol: str) -> float:
        symbol = symbol.replace("/", "")
        return float(self.exchange.fetch_ticker(symbol)['info']['last_price']) * 1.01

    def get_balance(self):
        balance = 0
        if self.target == "SPOT":
            info = self.exchange.private_get_spot_v1_account()['result']['balances']
            balance = [coin for coin in info if coin['coin'] == 'USDT'][0]['free']
        elif self.target == "FUTURE":
            balance = self.exchange.fetch_balance()['free']['USDT']
        logging.info(f"Balance remain: {balance}")
        return float(balance)

    def get_margin(self, symbol: str) -> float:
        margin = None
        if self.target == "FUTURE":
            info = self.exchange.fetch_balance()
            maintenance_margin = float(info.get('info').get('result').get('USDT').get('position_margin'))
            margin_balance = float(info.get('info').get('result').get('USDT').get('available_balance'))
            if margin_balance == 0:
                marginRatio = 0
            else:
                marginRatio = maintenance_margin / margin_balance
            margin = marginRatio

        logging.info(f"Margin level/ratio: {margin}")
        return margin

    def percentage_quantity(self):
        if self.use_all_collateral:
            balance = self.get_balance()
            quantity = balance
        else:
            quantity = self.quantity
            
        return float(quantity)
            
        
    def create_market_buy(self, symbol: str, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        quantity = self.percentage_quantity()
        price = self.get_price(symbol)
        amount = quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        
        if tp_price is None:
            tp_price = price * (1 + take_profit)
        if sl_price is None:
            sl_price = price * (1 - stop_loss)

        sl_price = max(sl_price, price * 0.01)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))
        
        logging.info(f"""
            Market Buy {symbol}
            price : {price}
            Amount : {amount}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        params=self.get_position_param(symbol, "Buy", tp_price, sl_price)
        order = self.exchange.createMarketBuyOrder(symbol, amount, params)
        logging.info(f"Open average price : {order['average']}")
        return order

    def create_limit_buy(self, symbol: str, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        quantity = self.percentage_quantity()
        price = self.get_price(symbol)
        amount = quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        
        if tp_price is None:
            tp_price = price * (1 + take_profit)
        if sl_price is None:
            sl_price = price * (1 - stop_loss)
            
        sl_price = max(sl_price, price * 0.01)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))
              
        logging.info(f"""
            Limit Buy {symbol}
            Open price : {price}
            Amount : {amount}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        
        params = self.get_position_param(symbol, "Buy", tp_price, sl_price)
        order = self.exchange.createLimitBuyOrder(symbol, amount, price, params)
        order["average"] = float(order.get("price", price))
        return order

    def create_market_sell(self, symbol: str, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        quantity = self.percentage_quantity()
        price = self.get_price(symbol)
        amount = quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        
        if tp_price is None:
            tp_price = price * (1 - take_profit)
        if sl_price is None:
            sl_price = price * (1 + stop_loss)

        tp_price = max(price * 0.01, tp_price)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))
        
        logging.info(f"""
            Market Sell {symbol}
            Amount : {amount}
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        
        params = self.get_position_param(symbol, "Sell", tp_price, sl_price)
        order = self.exchange.createMarketSellOrder(symbol, amount, params)
        logging.info(f"Sell average price : {order['average']}")
        return order

    def create_limit_sell(self, symbol: str, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        quantity = self.percentage_quantity()
        price = self.get_price(symbol)
        amount = quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        
        if tp_price is None:
            tp_price = price * (1 - take_profit)
        if sl_price is None:
            sl_price = price * (1 + stop_loss)

        tp_price = max(price * 0.01, tp_price)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))
        
        logging.info(f"""
            Limit Sell {symbol}
            Open price : {price}
            Amount : {amount}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        params = self.get_position_param(symbol, "Sell", tp_price, sl_price)
        order = self.exchange.createLimitSellOrder(symbol, amount, price, params)
        order["average"] = float(order.get("price", price))
        return order

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
            symbol = symbol.replace("/", "")
            position = [position for position in self.exchange.private_linear_get_position_list().get('result') if position.get('data').get('symbol') == symbol][0]
            if position.get('data').get('symbol') == symbol and position.get('side') != 'None':
                side = position.get('data').get('side')
                logging.info(f"{symbol} has {side} position.")
                side_map = {
                    "BUY": ("BUY", "LONG"),
                    "SELL": ("SELL", "SHORT")
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

        if action == "Sell" and self.target != "FUTURE":
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
        stop_loss = order_info.get("stop_loss")
        take_profit = order_info.get("take_profit")
        tp_price = order_info.get("scalp_take_profit")
        sl_price = order_info.get("scalp_stop_loss")
        logging.info(f"Symbol: {symbol}, Action: {action}")
        self.validate_order(symbol, action)

        open_order = None
        if action == "BUY":
            if self.order_type == "LIMIT":
                open_order = self.create_limit_buy(symbol, take_profit, stop_loss, tp_price, sl_price)
            elif self.order_type == "MARKET":
                open_order = self.create_market_buy(symbol, take_profit, stop_loss, tp_price, sl_price)
        elif action == "SELL":
            if self.order_type == "LIMIT":
                open_order = self.create_limit_sell(symbol, take_profit, stop_loss, tp_price, sl_price)
            elif self.order_type == "MARKET":
                open_order = self.create_market_sell(symbol, take_profit, stop_loss, tp_price, sl_price)
        return open_order
