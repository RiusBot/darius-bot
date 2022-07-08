import re
from .base import BaseParser


class AirforceParser(BaseParser):

    def __init__(self):
        self.name = "SPACEFORCE"

    def parse_symbol(self, message: str):
        text = message.strip().split('\n')
        title = text[0]
        info = {i.split(':')[0]: i.split(':')[1] for i in text[2:]}
        return info["標的"].replace("USDT", "")

    def parse_action(self, message: str):
        text = message.strip().split('\n')
        title = text[1]
        if "開倉" in title:
            return "SELL"
        elif "平倉" in title:
            return "BUY"
        
    def valid(self, entry, value):
        if entry is None:
            return True
        if value < (entry * 0.5):
            return False
        if value > (entry * 2):
            return False
        return True

    def parse_price(self, message: str):
        entry = None
        stop_loss = None
        take_profit = None
        func = max if self.action == "BUY" else min

        text = message.strip().split('\n')
        info = {i.split(':')[0]: i.split(':')[1] for i in text[2:]}
        stop_loss = float(info.get('止損', 0))
        take_profit = float(info.get('止盈', 0))
        entry = float(info.get('當前價位', 0))

        if take_profit and entry and (not stop_loss):
            stop_loss = entry + entry - take_profit
        
        if stop_loss and entry and (not take_profit):
            take_profit = entry + (entry - stop_loss) * 3

        self.entry = entry
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        return entry, stop_loss, take_profit, None
