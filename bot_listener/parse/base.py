import datetime
import logging
from abc import ABC, abstractmethod


class BaseParser(ABC):

    def parse(self, event):
        try:
            channel = event.chat.title
            content = event.text
            message_timestamp = event.date
            recieve_timestamp = datetime.datetime.now()
            symbol = self.parse_symbol(event.text)
            action = self.parse_action(event.text)
            return {
                "channel": channel,
                "content": content,
                "message_timestamp": message_timestamp,
                "recieve_timestamp": recieve_timestamp,
                "symbol": symbol,
                "action": action,
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
