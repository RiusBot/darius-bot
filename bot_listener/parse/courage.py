import re
import json
import base64
import logging
import functools
from .base import BaseParser


class CourageParser(BaseParser):

    def __init__(self):
        self.name = "COURAGE"

    def parse_symbol(self, message: str):
        symbol = json.loads(message)['Symbol']  # DOT/USDT 4H BINANCE
        symbol = symbol.split(' ')[0].split('/')[0]
        return symbol

    def parse_action(self, message: str):
        print(json.loads(message))
        return json.loads(message)['Side']
