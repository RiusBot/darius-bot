import re
import json
from .base import BaseParser


class CtaParser(BaseParser):

    def __init__(self, action: str, state: dict):
        self.name = "CTA"
        self.action = action
        self.state = state

    def parse_symbol(self, message: str):
        info = json.loads(message)
        symbol_list = []

        all_symbol = (set(info.keys()) | set(self.state.keys()))
        for symbol in all_symbol:
            amount = float(info.get(symbol, 0)) - float(self.state.get(symbol, 0))
            amount = round(amount, 4)
            symbol = symbol.replace("USDT", "").replace("BUSD", "")
            if self.action == "BUY" and amount > 0:
                symbol_list.append(symbol)
            elif self.action == "SELL" and amount < 0:
                symbol_list.append(symbol)

        # for symbol, amount in info.items():
        #     amount = float(amount)
        #     symbol = symbol.replace("USDT", "").replace("BUSD", "")
        #     if self.action == "BUY" and amount > 0:
        #         symbol_list.append(symbol)
        #     elif self.action == "SELL" and amount < 0:
        #         symbol_list.append(symbol)

        return symbol_list

    def parse_action(self, message: str):
        return self.action

    def parse_quantity(self, message: str, symbol_list: list):
        info = json.loads(message)
        amount_list = []

        all_symbol = (set(info.keys()) | set(self.state.keys()))
        for symbol in all_symbol:
            amount = float(info.get(symbol, 0)) - float(self.state.get(symbol, 0))
            amount = round(amount, 4)
            if self.action == "BUY" and amount > 0:
                amount_list.append(amount)
            elif self.action == "SELL" and amount < 0:
                amount_list.append(amount)

        # for symbol, amount in info.items():
        #     amount = float(amount)
        #     if self.action == "BUY" and amount > 0:
        #         amount_list.append(amount)
        #     elif self.action == "SELL" and amount < 0:
        #         amount_list.append(amount)

        return amount_list
