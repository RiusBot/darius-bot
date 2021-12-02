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
            symbol = self.parse_symbol(event.text)
            action = self.parse_action(event.text)
            entry, stop_loss, take_profit, price = self.parse_price(event.text)
            return {
                "channel": channel,
                "content": content,
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

    def parse_price(self):
        return None, None, None, None
