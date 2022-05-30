import ccxt
import json
import logging
from typing import List, Dict, Tuple

from .base import Base


class OkxClient(Base):

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
            "password": config["password"],
            'options': options,
            'headers': headers
        })

        try:
            self.exchange.check_required_credentials()
        except Exception as e:
            logging.error(f"Authenticate Requirements: {json.dumps(self.exchange.requiredCredentials, indent=4)}")
            raise e

        self.markets = self.exchange.loadMarkets(True)
        self.market_postprocess()

    def market_postprocess(self):
        pass
    
    def get_position_param(self, side: str):
        if self.target == "FUTURE":
            return {"posSide": self.get_position_side(side)}
        else:
            return {}
    
    def get_position_mode(self):
        # true: hedge (long_short_mode), false: one-way (net_mode)
        return self.exchange.okx.private_get_account_config()['data'][0]['posMode'] == "long_short_mode"
    
    def get_position_side(self, side: str):
        if self.get_position_mode():
            if side == "BUY":
                return "long"
            else:
                return "short"
        else:
            return "net"
        
    def make_symbol(self, symbol: str):
        return f"{symbol}/USDT"

    def get_volume(self, symbol: str) -> float:
        try:
            return float(okx.fetchTicker(symbol)['info']['volCcy24h'])
        except Exception:
            logging.excpetion("")
            logging.error("get volume failed")
            
    def get_price(self, symbol: str) -> float:
        symbol = symbol.replace("/", "")
        return float(self.exchange.fetchTicker(symbol)['info']["last"])