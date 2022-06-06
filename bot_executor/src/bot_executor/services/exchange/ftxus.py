import ccxt
import json
import logging
from typing import List, Dict, Tuple

from .ftx import FtxClient
from bot_executor.services.exchange import ftx_markets


class FtxusClient(FtxClient):

    def __init__(self, config: dict):
        super().__init__(config)

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

        global ftx_markets
        if ftx_markets:
            self.markets = ftx_markets
        else:
            self.markets = self.exchange.loadMarkets(True)
            ftx_markets = self.markets

        self.markets = {value.get('id', key): value for key, value in self.markets.items()}
        self.exchange.markets = self.markets
