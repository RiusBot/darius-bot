import re
import json
from .base import BaseParser


class CtaParser(BaseParser):

    def __init__(self, action: str):
        self.name = "CTA"
        self.action = action

    def parse_symbol(self, message: str):
        info = json.loads(message)
        symbol_list = []
        for symbol, amount in info.items():
            if self.action == "BUY" and amount > 0:
                symbol_list.append(symbol)
            elif self.action == "SELL" and amount < 0:
                symbol_list.append(symbol)
        return symbol_list

    def parse_action(self, message: str):
        return self.action
