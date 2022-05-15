class Base():
    
    def clean_limit_order(self, open_order: str, symbol: str):
        result = None
        symbol = self.make_symbol(symbol)

        if open_order:
            order_info = self.exchange.fetchOrder(open_order, symbol)
            if order_info["status"] == "open":
                result = "canceled"
                self.exchange.cancelOrder(order_info.get('id'), symbol)
            else:
                result = order_info["status"]

        return result
