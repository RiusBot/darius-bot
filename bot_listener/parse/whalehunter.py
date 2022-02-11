import re
from .base import BaseParser


class WhalehunterParser(BaseParser):

    def __init__(self):
        self.name = "WHALE"

    def parse_symbol(self, message: str):
        action = self.parse_action(message)
        idx = 0 if action == "SELL" else 1
        symbol_list = re.findall('#[^\s]+', message)
        symbol_list = [i.replace('#', '') for i in symbol_list]
        if symbol_list:
            return symbol_list[idx]

    def parse_action(self, message: str):
        if "📈" in message:
            return "BUY"
        elif "📉" in message:
            return "SELL"
