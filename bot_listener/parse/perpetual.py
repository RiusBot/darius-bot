import re
from .base import BaseParser


class PerpetualParser(BaseParser):

    def parse_symbol(self, message: str):
        symbol_list = re.findall('#[^\s]+', message)
        symbol_list = [i.replace('#', '') for i in symbol_list]
        if symbol_list:
            return symbol_list[0]

    def parse_action(self, message: str):
        if "看漲" in message:
            return "BUY"
        elif "看跌" in message:
            return "SELL"
