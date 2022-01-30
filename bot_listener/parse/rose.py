import re
import json
import base64
import logging
import functools
from .base import BaseParser


class RoseParser(BaseParser):

    def __init__(self):
        self.name = "ROSE"

    def parse_content(self, message: str):
        try:
            message = base64.b64decode(message.encode("ascii")).decode("ascii")
            return message
        except Exception:
            # logging.exception("")
            logging.error("Not Rose encode message.")
            return message

    def parse_symbol(self, message: str):
        try:
            pro_message = json.loads(message)
            if pro_message:
                symbol_list = pro_message["symbol_list"]
                if symbol_list:
                    tmp = []
                    for symbol in symbol_list:
                        symbol = symbol.replace("USDT", "")
                        symbol = re.compile('[^a-zA-Z0-9]').sub('', symbol)
                        tmp.append(symbol)
                    return tmp
        except Exception as e:
            logger.error(str(e))

    def parse_action(self, message: str):
        try:
            pro_message = json.loads(message)
            if pro_message:
                action = pro_message.get("action")
                if isinstance(action, str):
                    action = action.upper()
                return action
        except Exception as e:
          logger.error(str(e))
