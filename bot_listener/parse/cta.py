import re
import json
import logging
from .base import BaseParser


class CtaParser(BaseParser):

    def __init__(self, action: str, usdt_state: dict, busd_state: dict, quote: str):
        self.name = "CTA"
        self.action = action
        self.usdt_state = usdt_state
        self.busd_state = busd_state
        self.quote = quote
        if quote == 'BUSD':
            self.state = busd_state
            self.op_state = usdt_state
        elif quote == 'USDT':
            self.state = usdt_state
            self.op_state = busd_state

    def parse_symbol(self, message: str):
        info = json.loads(message)
        symbol_list = []
        all_symbol = (set(info.keys()) | set(self.state.keys()) )

        for symbol in all_symbol:
            op_symbol = symbol.replace("USDT", "BUSD") if self.quote == "USDT" else symbol.replace("BUSD", "USDT")
            # logging.info(f"{symbol} {float(info.get(symbol, 0))}, {op_symbol} {float(self.op_state.get(op_symbol, 0))}")

            amount = float(info.get(symbol, 0)) + float(self.op_state.get(op_symbol, 0))
            amount = round(amount, 4)

            symbol = symbol.replace("USDT", "").replace("BUSD", "")
            if self.action == "BUY" and amount > 0:
                symbol_list.append(symbol)
            elif self.action == "SELL" and amount <= 0:
                symbol_list.append(symbol)

        return symbol_list

    def parse_action(self, message: str):
        return self.action

    def parse_quantity(self, message: str, symbol_list: list):
        info = json.loads(message)
        amount_list = []
        all_symbol = (set(info.keys()) | set(self.state.keys()) )

        for symbol in all_symbol:
            op_symbol = symbol.replace("USDT", "BUSD") if self.quote == "USDT" else symbol.replace("BUSD", "USDT")
            logging.info(f"{symbol} {float(info.get(symbol, 0))}, {op_symbol} {float(self.op_state.get(op_symbol, 0))}")

            amount = float(info.get(symbol, 0)) + float(self.op_state.get(op_symbol, 0))
            amount = round(amount, 4)
            if self.action == "BUY" and amount > 0:
                amount_list.append(amount)
            elif self.action == "SELL" and amount <= 0:
                amount_list.append(amount)

        return amount_list
