import datetime
import logging
from abc import ABC, abstractmethod


class BaseParser(ABC):

    def parse(self, event):
        try:
            # channel = event.chat.title
            channel = self.name
            content = self.parse_content(event.text)
            message_timestamp = event.date.timestamp()
            recieve_timestamp = datetime.datetime.now().timestamp()

            try:
                symbol = self.parse_symbol(content)
                if not isinstance(symbol, list):
                    symbol = [symbol]
            except Exception:
                symbol = None
                logging.error("parse symbol error")
                logging.exception("")

            try:
                action = self.parse_action(content)
                self.action = action
            except Exception:
                action = None
                logging.error("parse action error")
                logging.exception("")

            try:
                entry, stop_loss, take_profit, price = self.parse_price(content)
            except Exception:
                entry, stop_loss, take_profit, price = None, None, None, None
                logging.error("parse price error")
                logging.exception("")

            try:
                quantity_list = self.parse_quantity(content, symbol)
            except Exception:
                quantity_list = [None for i in symbol]
                logging.error("parse quantity error")
                logging.exception("")

            return {
                "channel": channel,
                "content": content[:1024],
                "message_timestamp": message_timestamp,
                "recieve_timestamp": recieve_timestamp,
                "symbol": symbol,
                "action": action,
                "quantity": quantity_list,
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "price": price
            }
        except Exception:
            logging.error("Parser error.")
            logging.exception("")

    @abstractmethod
    def parse_symbol(self):
        # return token
        raise NotImplementedError

    @abstractmethod
    def parse_action(self):
        raise NotImplementedError

    def parse_quantity(self, message: str, symbol_list):
        return [None for i in symbol_list]

    def parse_price(self, message: str):
        # entry, stop_loss, take_profit, price
        return None, None, None, None

    def parse_content(self, content: str):
        return content
