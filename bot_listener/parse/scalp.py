import re
from .base import BaseParser


class ScalpParser(BaseParser):

    def __init__(self):
        self.name = "DAILYSCALP"

    def parse_symbol(self, message: str):
        tmp = message.split('\n')[0].split(' ')[0]
        tmp = re.compile('[^a-zA-Z0-9]').sub('', tmp)
        return tmp.replace("USDT", "")

    def parse_action(self, message: str):
        if "SHORT" in message.upper():
            return "SELL"
        if "LONG" in message.upper():
            return "BUY"
        if self.take_profit > self.entry:
            return "BUY"
        else:
            return "SELL"
        
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

        for line in message.split('\n')[1:]:
            try:
                key, value = line.split(':')
                value = value.replace('/', ' ')
                value = [float(i) for i in value.split(' ') if (i and valid(entry, float(i)))]

                if "target" in key.lower() or "tp" in key.lower():
                    take_profit = func(value)
                elif "entry" in key.lower():
                    entry = func(value)
                elif "sl" in key.lower():
                    stop_loss = func(value)
            except Exception:
                pass

        if take_profit and entry and (not stop_loss):
            stop_loss = entry + entry - take_profit
        
        if stop_loss and entry and (not take_profit):
            take_profit = entry + (entry - stop_loss) * 3

        self.entry = entry
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        return entry, stop_loss, take_profit, None
