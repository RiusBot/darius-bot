import json
import base64
import logging
import functools
from .base import BaseParser


class RoseParser(BaseParser):

    @functools.lru_cache(maxsize=None)
    def decode(self, message: str):
        try:
            message = base64.b64decode(message.encode("ascii")).decode("ascii")
            return json.loads(message)
        except Exception:
            # logging.exception("")
            logging.error("Not Rose encode message.")

    def parse_symbol(self, message: str):
        pro_message = self.decode(message)
        if pro_message:
            symbol_list = pro_message["symbol_list"]
            if symbol_list:
                symbol = symbol_list[0]
                symbol = symbol.replace("USDT", "")
                symbol = re.compile('[^a-zA-Z0-9]').sub('', symbol)
                return symbol

    def parse_action(self, message: str):
        pro_message = self.decode(message)
        if pro_message:
            return pro_message.get("action")
