import ccxt
import json
import logging
from typing import List, Dict, Tuple

from .ftx import FtxClient


class FtxusClient(FtxClient):

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
        self.subaccount = config.get("subaccount")

        options = {
            "defaultType": self.target.lower(),
            "adjustForTimeDifference": True,
            "verbose": True
        }
        headers = {}
        if self.subaccount:
            headers = {
                'FTX-SUBACCOUNT': self.subaccount
            }
            logging.info(f"headers: {headers}")
        self.exchange = ccxt.ftxus({
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
        self.markets = {value.get('id', key): value for key, value in self.markets.items()}
        self.exchange.markets = self.markets
