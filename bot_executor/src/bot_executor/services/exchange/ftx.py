import ccxt
import json
import logging
from copy import deepcopy
from typing import List, Dict, Tuple

from .base import Base
from bot_executor.services.exchange import ftx_markets


class FtxClient(Base):

    def __init__(self, config: dict):
        super().__init__(config)
        self.externalReferralProgram = None
        self.quote = self.others.get('quote', 'USD')

        self.options.update({
            "defaultType": self.target.lower(),
            "adjustForTimeDifference": True,
            "verbose": True
        })
        if self.subaccount:
            self.headers['FTX-SUBACCOUNT'] = self.subaccount

        self.exchange = ccxt.ftx({
            "enableRateLimit": True,
            "apiKey": config["api_key"],
            "secret": config["api_secret"],
            'options': self.options,
            'headers': self.headers,
        })

        try:
            self.exchange.check_required_credentials()
        except Exception as e:
            logging.error(f"Authenticate Requirements: {json.dumps(self.exchange.requiredCredentials, indent=4)}")
            raise e

        self.load_markets()
        self.markets = {value.get('id', key): value for key, value in self.markets.items()}
        self.exchange.markets = self.markets

    def load_markets(self):
        global ftx_markets
        if ftx_markets:
            self.markets = ftx_markets
            self.exchange.markets = ftx_markets
        else:
            self.markets = self.exchange.loadMarkets(True)
            ftx_markets = deepcopy(self.exchange.markets)
    
    def make_symbol(self, symbol: str):
        if self.target != "FUTURE":
            return f"{symbol}/{self.quote}"
        else:
            return f"{symbol}-PERP"
    
    def get_volume(self, symbol: str) -> float:
        try:
            symbol = symbol.replace("USDT", "USD")
            market = self.exchange.markets[symbol]
            info = market["info"]
            return float(info["volumeUsd24h"])
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")

    def get_price(self, symbol: str) -> float:
        symbol = symbol.replace("USDT", "USD")
        return float(self.exchange.fetchTicker(symbol)['bid']) * 1.01

    def get_balance(self):
        if self.balance is None:
            balance = 0
            info = self.exchange.fetch_balance()["info"]
            for coin in info["result"]:
                if coin['coin'] == self.quote:
                    balance = coin["total"]
            self.balance = float(balance)
        return self.balance

    def get_position(self, symbol: str, action: str):
        if self.target != "FUTURE":
            token = symbol.split('/')[0]
            asset = self.exchange.fetch_balance()["total"]
            amount = float(asset.get(token, 0))
            if amount > 0:
                price = self.get_price(symbol)
                notional = amount * price
                side = 'BUY' if amount > 0 else "SELL"
                if side == action:
                    return {
                        'symbol': symbol,
                        'amount': amount,
                        'notional': notional,
                        'side': side,
                        'info': {'side': side.lower()}
                    }
        elif self.target == "FUTURE":
            positions = self.exchange.fetchPositions()
            for position in positions:
                if "symbol" in position:
                    info = position.get("info", {})
                    if info.get('future') == symbol and info.get('entryPrice') and info.get('side') == action.lower():
                        return position

    def close_position(self, symbol: str, action: str, amount: float = None):
        position = self.get_position(symbol, action)
        if position is None:
            return

        if amount is None:
            if self.target == "FUTURE":
                amount = position.get('contracts', 0)
            else:
                amount = position.get('amount', 0)

        side = position['info']['side']
        if side == 'buy':
            self.create_market_sell(symbol, amount)
        elif side == 'sell':
            self.create_market_buy(symbol, amount)
        else:
            raise Exception(f"Unknown side {side}")

    def close_all_orders(self):
        pass

    def get_margin(self, symbol: str) -> float:
        margin = self.exchange.private_get_account()["result"]["marginFraction"]
        return 999 if margin is None else float(margin)

    def create_market_buy(self, symbol: str, amount: float = None):
        price = self.get_price(symbol)
        if amount is None:
            amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Market Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createMarketBuyOrder(symbol, amount, params={'externalReferralProgram': self.externalReferralProgram})
        if order["price"] is None:
            order["price"] = price
        logging.info(f"Open average price : {order['average']}")
        return order

    def create_limit_buy(self, symbol: str, amount: float = None, price: float = None):
        if price is None:
            price = self.get_price(symbol) * 1.01
        if amount is None:
            amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Limit Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createLimitBuyOrder(
            symbol,
            amount,
            price,
            params={'ioc': (self.target != "FUTURE"), 'externalReferralProgram': self.externalReferralProgram}
        )
        order["average"] = order.get("price", price)
        if self.target != "FUTURE":
            order["amount"] = float(order.get("filled", 0))
        return order

    def create_market_sell(self, symbol: str, amount: float = None):
        price = self.get_price(symbol)
        if amount is None:
            amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Market Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createMarketSellOrder(symbol, amount)
        if order["price"] is None:
            order["price"] = price
        logging.info(f"Sell average price : {order['average']}")
        return order

    def create_limit_sell(self, symbol: str, amount: float = None, price: float = None):
        if price is None:
            price = self.get_price(symbol) * 0.99
        if amount is None:
            amount = self.quantity / price * self.leverage
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Limit Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        order = self.exchange.createLimitSellOrder(
            symbol,
            amount,
            price,
            params={'ioc': (self.target != "FUTURE"), 'externalReferralProgram': self.externalReferralProgram}
        )
        order["average"] = order.get("price", price)
        if self.target != "FUTURE":
            order["amount"] = float(order.get("filled", 0))
        return order

    def create_oco_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        price = float(open_order["price"])
        open_order = self.exchange.fetchOrder(open_order["id"])
        amount = float(open_order["amount"])
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if open_order.get("average") is not None:
            price = float(open_order["average"])
        elif open_order.get("price") is not None:
            price = float(open_order["price"])

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
            Amount: {amount},
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        
        if amount <= 0:
            return tp_order, sl_order

        params = {
            "market": symbol,
            "side": "sell",
            "size": amount,
            "type": "takeProfit",
            "reduceOnly": True,
            'externalReferralProgram': self.externalReferralProgram
        }
        if self.take_profit_type != "TRAILING":
            params["triggerPrice"] = tp_price
            if self.take_profit_type == "LIMIT":
                params["orderPrice"] = tp_price
        else:
            params["type"] = "trailingStop"
            params["trailValue"] = price * (1 - take_profit) - price
        tp_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        params = {
            "market": symbol,
            "side": "sell",
            "size": amount,
            "type": "stop",
            "reduceOnly": True,
            'externalReferralProgram': self.externalReferralProgram
        }
        if self.stop_loss_type != "TRAILING":
            params["triggerPrice"] = sl_price
            if self.stop_loss_type == "LIMIT":
                params["orderPrice"] = sl_price
        else:
            params["type"] = "trailingStop"
            params["trailValue"] = price * (1 + stop_loss) - price
        sl_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        return tp_order.get("result"), sl_order.get("result")

    def create_oco_short_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        price = float(open_order["price"])
        open_order = self.exchange.fetchOrder(open_order["id"])
        amount = float(open_order["amount"])
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if open_order.get("average") is not None:
            price = float(open_order["average"])
        elif open_order.get("price") is not None:
            price = float(open_order["price"])

        if tp_price is None:
            tp_price = price * (1 - take_profit)
        if sl_price is None:
            sl_price = price * (1 + stop_loss)
        tp_price = max(price * 0.01, tp_price)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))

        tp_order = None
        sl_order = None
        logging.info(f"""
            Create OCO short order
            Amount: {amount},
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)
        if amount <= 0:
            return tp_order, sl_order

        params = {
            "market": symbol,
            "side": "buy",
            "size": amount,
            "type": "takeProfit",
            "reduceOnly": True,
            'externalReferralProgram': self.externalReferralProgram
        }
        if self.take_profit_type != "TRAILING":
            params["triggerPrice"] = tp_price
            if self.take_profit_type == "LIMIT":
                params["orderPrice"] = tp_price
        else:
            params["type"] = "trailingStop"
            params["trailValue"] = take_profit
        tp_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        params = {
            "market": symbol,
            "side": "buy",
            "size": amount,
            "type": "stop",
            "reduceOnly": True,
            'externalReferralProgram': self.externalReferralProgram
        }
        if self.stop_loss_type != "TRAILING":
            params["triggerPrice"] = sl_price
            if self.stop_loss_type == "LIMIT":
                params["orderPrice"] = sl_price
        else:
            params["type"] = "trailingStop"
            params["trailValue"] = stop_loss
        sl_order = self.exchange.private_post_conditional_orders(
            params=params
        )

        return tp_order.get("result"), sl_order.get("result")

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
        if margin < self.margin:
            return f"invalid margin. Current: {margin}, restrict: {self.margin}"

    def clean_oco_order(self, sl_order: str, tp_order: str, symbol: str):
        symbol = self.make_symbol(symbol)
        open_conditional_order_list = []
        ftx_response = self.exchange.private_get_conditional_orders({'market': symbol})
        if ftx_response.get('success'):
            open_conditional_order_list = ftx_response['result']
        else:
            logging.error(f"{ftx_response}")

        tp_closed = True
        sl_closed = True

        if tp_order:
            for order in open_conditional_order_list:
                if order['id'] == tp_order:
                    tp_closed = False
                    break

        if sl_order:
            for order in open_conditional_order_list:
                if order['id'] == sl_order:
                    sl_closed = False
                    break

        if tp_closed and not sl_closed:
            self.exchange.cancelOrder(sl_order, symbol, {'method': 'privateDeleteConditionalOrdersOrderId'})
            return "TP"
        
        if not tp_closed and sl_closed:
            self.exchange.cancelOrder(tp_order, symbol, {'method': 'privateDeleteConditionalOrdersOrderId'})
            return "SL"
        
        if tp_closed and sl_closed:
            # require check for tp or sl
            return "closed"

        buy_position = self.get_position(symbol, 'BUY')
        sell_position = self.get_position(symbol, 'SELL')
        if (not buy_position) and (not sell_position):
            if not sl_closed:
                self.exchange.cancelOrder(sl_order, symbol)
            if not tp_closed:
                self.exchange.cancelOrder(tp_order, symbol)
            return "closed"
