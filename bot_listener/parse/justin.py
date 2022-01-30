import re
import json
import ccxt
import base64
import logging
import functools
from .base import BaseParser


class JustinParser(BaseParser):

    def __init__(self, action):
        self.name = "JUSTIN"
        self.exchange = ccxt.binance({})
        self.exchange.loadMarkets()
        self.action = action

    def parse_symbol(self, message: str) -> list:
        if "【今日進場】" in message:
            message = re.compile('[^a-zA-Z0-9\n:：]').sub('', message)
            symbol_list = []
            lines = [i.strip() for i in message.split('\n') if i.strip()]
            for line in lines:
                if ":" in line or "：" in line:
                    continue
                symbol = [i.upper() for i in re.split(' |1|2|3', line.strip()) if i]
                if len(symbol) == 1 and self.action == "BUY":
                    symbol = symbol[0].upper()
                    if f"{symbol}/USDT" in self.exchange.markets:
                        symbol_list.append(symbol)
                elif len(symbol) == 2:
                    act = symbol[1].upper()
                    symbol = symbol[0].upper()
                    if ("L" in act and self.action == "BUY") or ("S" in act and self.action == "SELL"):
                        if f"{symbol}/USDT" in self.exchange.markets:
                            symbol_list.append(symbol)
            return symbol_list
        else:
            return []

    def parse_action(self, message: str):
        return self.action