from .base import BaseParser

class WhalehunterParser(BaseParser):
    
    def parse_symbol(self, message: str):
        symbol_list = re.findall('#[^\s]+', message)
        symbol_list = [i.replace('#', '') for i in symbol_list]
        if symbol_list:
            return symbol_list[1]
    
    def parse_action(self, message: str):
        if "📈" in message:
            return "BUY"
        elif "📉" in message:
            return "SELL"
