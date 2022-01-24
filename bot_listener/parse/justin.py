import re
import json
import ccxt
import base64
import logging
import functools
from .base import BaseParser


class JustinParser(BaseParser):

    def __init__(self):
        self.name = "JUSTIN"
        self.exchange = ccxt.binance({})
        self.exchange.loadMarkets()

    def parse_symbol(self, message: str):
        message = re.compile('[^a-zA-Z0-9\n]').sub('', message)
        symbol_list = []
        lines = [i.strip() for i in message.split('\n') if i.strip()]
        for line in lines:
            symbol = ""
            for c in line:
                if c.isalpha():
                    symbol += c
                else:
                    break
            symbol = symbol.upper()
            if f"{symbol}/USDT" in self.exchange.markets:
                symbol_list.append(symbol)
        return symbol_list

    def parse_action(self, message: str):
        if "今天" in message and "進" in message:
            return "BUY"
        elif "今天" in message and "出" in message:
            return "SELL"