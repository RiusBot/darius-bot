import ccxt
import json
import logging
from copy import deepcopy
from typing import List, Dict, Tuple

from .base import Base
from bot_executor.services.exchange import okx_markets


class OkxClient(Base):

    def __init__(self, config: dict):
        super().__init__(config)
        self.quote = self.others.get('quote', 'USDT')

        defaultType = {
            'SPOT': 'SPOT',
            'FUTURE': 'SWAP',
            'MARGIN': 'MARGIN'
        }.get(self.target.upper())

        if self.config.get("testnet", False) == True:
            self.headers.update({'x-simulated-trading': '1'})

        self.options.update({
            "defaultType": defaultType,
            "adjustForTimeDifference": True,
            "verbose": True,
            'brokerId': 'a8a0f2138d1bBCDE'
        })

        self.exchange = ccxt.okx({
            "enableRateLimit": True,
            "apiKey": config["api_key"],
            "secret": config["api_secret"],
            "password": config.get("password"),
            'options': self.options,
            'headers': self.headers
        })

        try:
            self.exchange.check_required_credentials()
        except Exception as e:
            logging.error(f"Authenticate Requirements: {json.dumps(self.exchange.requiredCredentials, indent=4)}")
            raise e

        self.load_markets()
        self.market_postprocess()
        self.account_config = self.exchange.private_get_account_config()['data'][0]
        self.set_tdmode()

    def load_markets(self):
        global okx_markets
        if okx_markets:
            self.markets = okx_markets
            self.exchange.markets = okx_markets
        else:
            self.markets = self.exchange.loadMarkets(True)
            okx_markets = deepcopy(self.exchange.markets)
    
    def market_postprocess(self):
        pass

    def set_tdmode(self):
        if self.account_config['acctLv'] == "1":
            self.tdMode = "cash"
        else:
            self.tdMode = "cross"

    def get_position_mode(self):
        # true: hedge (long_short_mode), false: one-way (net_mode)
        return self.account_config['posMode'] == "long_short_mode"

    def get_position_side(self, side: str):
        if self.get_position_mode():
            if side == "BUY":
                return "long"
            else:
                return "short"
        else:
            return "net"

    def make_symbol(self, symbol: str):
        if self.target == "FUTURE":
            symbol = f"{symbol}/{self.quote}:{self.quote}"
        else:
            symbol = f"{symbol}/{self.quote}"
        return symbol

    def get_volume(self, symbol: str) -> float:
        try:
            return float(okx.fetchTicker(symbol)['info']['volCcy24h'])
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")

    def get_price(self, symbol: str) -> float:
        return float(self.exchange.fetchTicker(symbol)['info']["last"])

    def get_balance(self):
        if self.balance is None:
            balance = self.exchange.fetch_balance()
            if balance["info"]["data"][0]['adjEq']:
                balance = float(balance["info"]["data"][0]['adjEq'])
            else:
                balance = balance.get(self.quote, {}).get('total', 0)
            logging.debug(f"Balance remain: {balance}")
            self.balance = float(balance)
        return self.balance
    
    def close_all_orders(self, symbol=None):
        super().close_all_orders(symbol)

        okx_response = self.exchange.private_get_trade_orders_algo_pending(params={'ordType':"conditional"})
        if okx_response.get('code') == 0:
            open_conditional_order_list = ftx_response['data']
            open_conditional_order_list = [
                {'instId': order['instId'], 'algoId': order['algoId']}
                for order in open_conditional_order_list
            ]
            tmp.private_post_trade_cancel_algos(params=open_conditional_order_list)
        else:
            logging.error(f"{okx_response}")

        okx_response = self.exchange.private_get_trade_orders_algo_pending(params={'ordType':"oco"})
        if okx_response.get('code') == 0:
            open_conditional_order_list = ftx_response['data']
            open_conditional_order_list = [
                {'instId': order['instId'], 'algoId': order['algoId']}
                for order in open_conditional_order_list
            ]
            tmp.private_post_trade_cancel_algos(params=open_conditional_order_list)
        else:
            logging.error(f"{okx_response}")

        okx_response = self.exchange.private_get_trade_orders_algo_pending(params={'ordType':"trigger"})
        if okx_response.get('code') == 0:
            open_conditional_order_list = ftx_response['data']
            open_conditional_order_list = [
                {'instId': order['instId'], 'algoId': order['algoId']}
                for order in open_conditional_order_list
            ]
            tmp.private_post_trade_cancel_algos(params=open_conditional_order_list)
        else:
            logging.error(f"{okx_response}")

    def close_position(self, symbol: str, action: str, amount: float = None):
        position = self.get_position(symbol, action)
        if position is None:
            return
        
        if amount is None:
            if self.target == "FUTURE":
                amount = position.get('contracts', 0) * position.get('contractSize', 0)
            else:
                amount = abs(position.get('amount', 0))

        if self.target == "FUTURE":
            positionSide = position['info']['posSide']
            instId = position['info']['instId']
            mgnMode = position['info']['mgnMode']

            logging.info(f"Close future position. symbol: {symbol}, amount: {amount}, pos: {positionSide}")
            self.exchange.private_post_trade_close_position(params={
                'instId': instId,
                'mgnMode': mgnMode,
                'posSide': positionSide,
            })
        else:
            logging.info(f"Close spot position. symbol: {symbol}, amount: {amount}")
            if position['side'] == 'BUY':
                try:
                    self.create_market_sell(symbol, amount)
                except:
                    self.create_limit_sell(symbol, amount)
            elif position['side'] == 'SELL':
                try:
                    self.create_market_buy(symbol, amount)
                except:
                    self.create_limit_buy(symbol, amount)

    def get_margin(self, symbol: str) -> float:
        margin = self.exchange.fetch_balance()['info']['data'][0]['mgnRatio']
        margin = float(margin) if margin else float('inf')
        logging.debug(f"Margin level/ratio: {margin}")
        return margin

    def get_amount(self, symbol: str, amount: int):
        if self.target == "FUTURE":
            contract_size = float(self.markets[symbol]['contractSize'])
            return amount / contract_size
        else:
            return amount

    def create_market_buy(self, symbol: str, amount: float = None):
        price = self.get_price(symbol)
        if amount is None:
            amount = self.get_amount(symbol, self.quantity / price * self.leverage)
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Market Buy {symbol}
            price : {price}
            Amount : {amount}
        """)
        params = {
            'posSide': self.get_position_side("BUY"),
            'lever': self.leverage,
            'tdMode': self.tdMode,
        }
        order = self.exchange.createMarketBuyOrder(symbol, amount, params=params)
        order = self.exchange.fetchOrder(symbol=symbol, id=order['id'])
        return order

    def create_limit_buy(self, symbol: str, amount: float = None, price: float = None):
        if price is None:
            price = self.get_price(symbol) * 1.01
        if amount is None:
            amount = self.get_amount(symbol, self.quantity / price * self.leverage)
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Limit Buy {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        params = {
            'posSide': self.get_position_side("BUY"),
            'lever': self.leverage,
            'tdMode': self.tdMode
        }
        if self.target != "FUTURE":
            params["ordType"] = "ioc"
        order = self.exchange.createLimitBuyOrder(symbol, amount, price, params=params)
        order["average"] = float(order.get("price", price))
        if self.target != "FUTURE":
            order["amount"] = float(order.get("filled", 0))
        return order

    def create_market_sell(self, symbol: str, amount: float = None):
        price = self.get_price(symbol)
        if amount is None:
            amount = self.get_amount(symbol, self.quantity / price * self.leverage)
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Market Sell {symbol}
            Amount : {amount}
            Price: {price}
        """)
        params = {
            'posSide': self.get_position_side("SELL"),
            'lever': self.leverage,
            'tdMode': self.tdMode,
        }
        order = self.exchange.createMarketSellOrder(symbol=symbol, amount=amount, params=params)
        order = self.exchange.fetchOrder(symbol=symbol, id=order['id'])
        print(order)
        return order

    def create_limit_sell(self, symbol: str, amount: float = None, price: float = None):
        if price is None:
            price = self.get_price(symbol) * 0.99
        if amount is None:
            amount = self.get_amount(symbol, self.quantity / price * self.leverage)
        price = float(self.exchange.price_to_precision(symbol, price))
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        if amount <= 0 or (self.quantity * self.leverage < 10):
            return "quantity too small to make order"
        logging.info(f"""
            Limit Sell {symbol}
            Open price : {price}
            Amount : {amount}
        """)
        params = {
            'posSide': self.get_position_side("SELL"),
            'lever': self.leverage,
            'tdMode': self.tdMode
        }
        if self.target != "FUTURE":
            params["ordType"] = "ioc"
        order = self.exchange.createLimitSellOrder(symbol, amount, price, params=params)
        order["average"] = float(order.get("price", price))
        if self.target != "FUTURE":
            order["amount"] = float(order.get("filled", 0))
        return order

    def create_oco_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):
        
        skip_tp = True if (take_profit == 0 and tp_price is None) else False
        skip_sl = True if (stop_loss == 0 and sl_price is None) else False
        
        amount = float(open_order["amount"])
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        price = float(open_order.get("average", open_order.get("price", self.get_price(symbol))))
        if tp_price is None:
            tp_price = price * (1 + take_profit)
        if sl_price is None:
            sl_price = price * (1 - stop_loss)

        sl_price = max(sl_price, price * 0.01)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))

        logging.info(f"""
            Create OCO order
            Amount: {amount}
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)

        tp_order = None
        sl_order = None
        if amount <= 0:
            logging.error(f"amount {amount} <= 0")
            return tp_order, sl_order

        params = {
            'instId': self.markets[symbol]['id'],
            'tdMode': self.tdMode,
            'side': 'sell',
            'posSide': self.get_position_side("SELL"),
            'sz': amount,
        }
        sl_params, tp_params = self.create_oco_params(params, sl_price, tp_price, price, take_profit, stop_loss)
        if not skip_sl:
            sl_order = self.exchange.private_post_trade_order_algo(params=sl_params)
        if self.take_profit_type != "TRAILING":
            if not skip_tp:
                tp_order = self.exchange.private_post_trade_order_algo(params=tp_params)
        return tp_order, sl_order

    def create_oco_short_order(self, symbol: str, open_order: dict, take_profit: float, stop_loss: float, tp_price: float, sl_price: float):

        skip_tp = True if (take_profit == 0 and tp_price is None) else False
        skip_sl = True if (stop_loss == 0 and sl_price is None) else False

        amount = float(open_order["amount"])
        amount = float(self.exchange.amount_to_precision(symbol, amount))
        price = float(open_order.get("average", open_order.get("price", self.get_price(symbol))))
        if tp_price is None:
            tp_price = price * (1 - take_profit)
        if sl_price is None:
            sl_price = price * (1 + stop_loss)

        tp_price = max(price * 0.01, tp_price)
        tp_price = float(self.exchange.price_to_precision(symbol, tp_price))
        sl_price = float(self.exchange.price_to_precision(symbol, sl_price))

        logging.info(f"""
            Create OCO short order
            Amount: {amount},
            Price: {price}
            Stop loss: {sl_price},
            Take profit : {tp_price}
        """)

        tp_order = None
        sl_order = None
        if amount <= 0:
            return tp_order, sl_order

        params = {
            'instId': self.markets[symbol]['id'],
            'tdMode': self.tdMode,
            'side': 'buy',
            'posSide': self.get_position_side("BUY"),
            'sz': amount,
        }
        sl_params, tp_params = self.create_oco_params(params, sl_price, tp_price, price, take_profit, stop_loss)
        if not skip_sl:
            sl_order = self.exchange.private_post_trade_order_algo(params=sl_params)
        if self.take_profit_type != "TRAILING":
            if not skip_tp:
                tp_order = self.exchange.private_post_trade_order_algo(params=tp_params)
        return tp_order, sl_order

    def create_oco_params(self, params: dict, sl_price: float, tp_price: float, price: float, take_profit: float, stop_loss: float):

        if self.stop_loss_type == "TRAILING":
            sl_params = {
                'callbackRatio': min(max(stop_loss, 0.001), 1),
                'activePx': price,
                'ordType': 'move_order_stop',
            }
        else:
            sl_params = {
                'slTriggerPx': sl_price,
                'slOrdPx': sl_price if self.stop_loss_type == "LIMIT" else -1,  # -1 for market close
                'ordType': 'conditional',
                'reduceOnly': (self.target != "SPOT"),
            }

        if self.take_profit_type == "TRAILING":
            tp_params = {
                'callbackRatio': min(max(take_profit, 0.001), 1),
                'activePx': price,
                'ordType': 'conditional',
            }
        else:
            tp_params = {
                'tpTriggerPx': tp_price,
                'tpOrdPx': tp_price if self.take_profit_type == "LIMIT" else -1,  # -1 for market close
                'ordType': 'conditional',
                'reduceOnly': (self.target != "SPOT"),
            }

        return {**params, **sl_params}, {**params, **tp_params}

    def validate_margin(self, symbol: str):
        margin = self.get_margin(symbol)
        if margin < self.margin:
            return f"invalid margin. Current: {margin}, restrict: {self.margin}"
        
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
        
        buy_position = self.get_position(symbol, 'BUY')
        sell_position = self.get_position(symbol, 'SELL')
        if (not buy_position) and (not sell_position):
            if sl_order_info["status"] == "open":
                self.exchange.cancelOrder(sl_order, symbol)
            if tp_order_info["status"] == "open":
                self.exchange.cancelOrder(tp_order, symbol)
            return "closed"
