import time
from abc import ABC, abstractmethod


class BaseParser(ABC):
    
    def parse(self, event):
        channel = event.chat.title
        content = event.text
        message_timestamp = event.date.timestamp()
        recieve_timestamp = time.time()
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
    
    @abstractmethod
    def parse_symbol(self):
        raise NotImplmentedError
        
    @abstractmethod
    def parse_action(self):
        raise NotImplmentedError