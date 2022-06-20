import ccxt
import json
import logging
from copy import deepcopy
from typing import List, Dict, Tuple

from .base import Base
from bot_executor.services.exchange import binance_spot_markets, binance_future_markets


class BinanceClient(Base):

    def __init__(self, config: dict):
        super().__init__(config)
        self.quote = self.others.get('quote', 'USDT')

        self.options.update({
            "defaultType": self.target.lower(),
            "adjustForTimeDifference": True,
            "verbose": True,
            'broker': {
                'spot': 'x-V9ZBVGB7',
                'margin': 'x-V9ZBVGB7',
                'future': 'x-61E2GsBt',
                'delivery': 'x-61E2GsBt',
            },
        })

        self.exchange = ccxt.binance({
            "enableRateLimit": True,
            "apiKey": config["api_key"],
            "secret": config["api_secret"],
            'options': self.options,
            'headers': self.headers
        })
        if self.config.get("testnet", False) == True:
            self.exchange.set_sandbox_mode(True)

        try:
            self.exchange.check_required_credentials()
        except Exception as e:
            logging.error(f"Authenticate Requirements: {self.exchange.requiredCredentials}")
            raise e

        self.load_markets()
        self.market_postprocess()
        self.scalp_quantity()

    def load_markets(self):

        global binance_spot_markets, binance_future_markets

        if self.target == "FUTURE":
            if binance_future_markets:
                self.markets = binance_future_markets
                self.exchange.markets = binance_future_markets
            else:
                self.markets = self.exchange.loadMarkets(True)
                binance_future_markets = deepcopy(self.exchange.markets)
        else:
            if binance_spot_markets:
                self.markets = binance_spot_markets
                self.exchange.markets = binance_spot_markets
            else:
                self.markets = self.exchange.loadMarkets(True)
                binance_spot_markets = deepcopy(self.exchange.markets)

    def market_postprocess(self):
        if self.target.lower() == "future":
            tmp = {
                f'SHIB/{self.quote}': self.markets.get(f"1000SHIB/{self.quote}"),
                f'XEC/{self.quote}': self.markets.get(f"1000XEC/{self.quote}"),
            }
            self.markets.update(tmp)
            self.exchange.markets.update(tmp)

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
        return f"{symbol}/{self.quote}"
    
    def get_volume(self, symbol: str) -> float:
        try:
            symbol = symbol.replace("/", "")
            return float(self.exchange.fapiPublic_get_ticker_24hr({'symbol': symbol})["volume"])
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")

    def get_price(self, symbol: str) -> float:
        symbol = symbol.replace("/", "")
        return float(self.exchange.fetchTicker(symbol)['info']["lastPrice"])

    def get_balance(self):
        balance = 0
        if self.target == "SPOT":
            assets = self.exchange.fetch_balance()["info"]["balances"]
            for asset in assets:
                if asset["asset"] == self.quote:
                    balance = asset["free"]
        elif self.target == "MARGIN":
            assets = self.exchange.fetch_balance()["info"]["userAssets"]
            for asset in assets:
                if asset["asset"] == self.quote:
                    balance = asset["free"]
        elif self.target == "FUTURE":
            balance = self.exchange.fetch_balance()["info"]['availableBalance']
        logging.debug(f"Balance remain: {balance}")
        return float(balance)
    
    def get_position(self, symbol: str):
        if self.target == "SPOT" or self.target == "MARGIN":
            token = symbol.split('/')[0]
            asset = self.exchange.fetch_balance()["total"]
            amount = float(asset.get(token, 0))
            price = self.get_price(symbol)
            notional = amount * price
            return {'notional': notional}
        elif self.target == "FUTURE":
            positions = self.exchange.fetchPositions()
            for position in positions:
                if position.get('symbol') == symbol and position.get('side'):
                    return position

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

        logging.debug(f"Margin level/ratio: {margin}")
        return margin

    def create_market_buy(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0:
            return "quantity too small to make order"
        logging.info(f"""
            Market Buy {symbol}
            price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createMarketBuyOrder(symbol, amount, params=self.get_position_param("BUY"))
        logging.info(f"Open average price : {order['average']}")
        return order

    def create_limit_buy(self, symbol: str):
        price = self.get_price(symbol) * 1.01
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0:
            return "quantity too small to make order"
        logging.info(f"""
            Limit Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        params = self.get_position_param("BUY")
        if self.target != "FUTURE":
            params["timeInForce"] = "IOC"
        order = self.exchange.createLimitBuyOrder(symbol, amount, price, params=params)
        order["average"] = float(order.get("price", price))
        if self.target != "FUTURE":
            order["amount"] = float(order.get("filled", 0))
        return order

    def create_market_sell(self, symbol: str):
        price = self.get_price(symbol)
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0:
            return "quantity too small to make order"
        logging.info(f"""
            Market Sell {symbol}
            Amount : {amount}
            Price: {price}
        """)
        order = self.exchange.createMarketSellOrder(symbol, amount, params=self.get_position_param("SELL"))
        logging.info(f"Sell average price : {order['average']}")
        return order

    def create_limit_sell(self, symbol: str):
        price = self.get_price(symbol) * 0.99
        amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0:
            return "quantity too small to make order"
        logging.info(f"""
            Limit Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        params = self.get_position_param("SELL")
        if self.target != "FUTURE":
            params["timeInForce"] = "IOC"
        order = self.exchange.createLimitSellOrder(symbol, amount, price, params=params)
        order["average"] = float(order.get("price", price))
        if self.target != "FUTURE":
            order["amount"] = float(order.get("filled", 0))
        return order

    def create_oco_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        amount = float(open_order["amount"]) * 0.995
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
            logging.info(f"amount {amount} <= 0")
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
                    "priceProtect": True,
                    "positionSide": self.get_position_side("SHORT")
                }
                if not self.get_position_mode():
                    tp_params["closePosition"] = (tp_order_type=="TAKE_PROFIT_MARKET")
            else:
                tp_params = {
                    "callbackRate": min(max(take_profit * 100, 0.1), 5),
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
                    "priceProtect": True,
                    "positionSide": self.get_position_side("SHORT")
                }
                if not self.get_position_mode():
                    sl_params["closePosition"] = (sl_order_type=="STOP_MARKET")
            else:
                sl_params = {
                    "callbackRate": min(max(stop_loss * 100, 0.1), 5),
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
        amount = float(open_order["amount"]) * 0.995
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
                    "priceProtect": True,
                    "positionSide": self.get_position_side("BUY")
                }
                if not self.get_position_mode():
                    tp_params["closePosition"] = (tp_order_type=="TAKE_PROFIT_MARKET")
            else:
                tp_params = {
                    "callbackRate": min(max(take_profit * 100, 0.1), 5),
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
                    "priceProtect": True,
                    "positionSide": self.get_position_side("BUY")
                }
                if not self.get_position_mode():
                    sl_params["closePosition"] = (sl_order_type=="STOP_MARKET")
            else:
                sl_params = {
                    "callbackRate": min(max(stop_loss * 100, 0.1), 5),
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

    def validate_margin(self, symbol: str):
        margin = self.get_margin(symbol)
        error_msg = f"invalid margin. Current: {margin}, restrict: {self.margin}"
        if self.target == "FUTURE":
            if margin > self.margin:
                return error_msg
        elif self.target == "MARGIN":
            if margin < self.margin:
                return error_msg

    def clean_oco_order(self, sl_order: str, tp_order: str, symbol: str):
        symbol = self.make_symbol(symbol)
        tp_order_info = {'status': 'unknown'}
        sl_order_info = {'status': 'unknown'}

        if tp_order:
            tp_order_info = self.exchange.fetchOrder(tp_order, symbol)

        if sl_order:
            sl_order_info = self.exchange.fetchOrder(sl_order, symbol)

        if tp_order_info["status"] == "closed" and sl_order_info["status"] == "open":
            self.exchange.cancelOrder(sl_order, symbol)
            return "TP"

        if sl_order_info["status"] == "closed" and tp_order_info["status"] == "open":
            self.exchange.cancelOrder(tp_order, symbol)
            return "SL"

        if sl_order_info["status"] == "closed" and tp_order_info["status"] == "open":
            return "closed"
