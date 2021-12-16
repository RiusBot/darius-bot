import datetime
import logging
from abc import ABC, abstractmethod


class BaseParser(ABC):

    def parse(self, event):
        try:
            channel = event.chat.title
            content = event.text
            message_timestamp = event.date.timestamp()
            recieve_timestamp = datetime.datetime.now().timestamp()

            try:
                symbol = self.parse_symbol(event.text)
            except Exception:
                symbol = None
                logging.error("parse symbol error")
                logging.exception("")

            try:
                action = self.parse_action(event.text)
            except Exception:
                action = None
                logging.error("parse action error")
                logging.exception("")

            try:
                entry, stop_loss, take_profit, price = self.parse_price(event.text)
            except Exception:
                entry, stop_loss, take_profit, price = None, None, None, None
                logging.error("parse price error")
                logging.exception("")

            return {
                "channel": channel,
                "content": content[:1024],
                "message_timestamp": message_timestamp,
                "recieve_timestamp": recieve_timestamp,
                "symbol": symbol,
                "action": action,
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
        raise NotImplementedError

    @abstractmethod
    def parse_action(self):
        raise NotImplementedError

    def parse_price(self, message: str):
        return None, None, None, None
