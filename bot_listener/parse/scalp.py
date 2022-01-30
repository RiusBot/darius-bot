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
        return "BUY"

    def parse_price(self, message: str):
        entry = None
        stop_loss = None
        take_profit = None

        for line in message.split('\n')[1:]:
            try:
                key, value = line.split(':')
                value = value.replace('/', ' ')
                if "target" in key.lower() or "tp" in key.lower():
                    take_profit = float(value.split(' ')[-1])
                elif "entry" in key.lower():
                    entry = float(value.split(' ')[-1])
                elif "sl" in key.lower():
                    stop_loss = float(value.split(' ')[-1])
            except Exception:
                pass

        if take_profit and entry and (not stop_loss):
            stop_loss = entry + entry - take_profit

        return entry, stop_loss, take_profit, None
