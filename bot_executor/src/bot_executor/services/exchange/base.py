class Base():

    def clean_oco_order(self, sl_order: str, tp_order: str, symbol: str):
        result = None
        symbol = self.make_symbol(symbol)

        if tp_order:
            tp_order_info = self.exchange.fetchOrder(tp_order, symbol)
            if tp_order_info["status"] == "closed":
                result = "TP"
                self.exchange.cancelOrder(sl_order, symbol)

        if sl_order:
            sl_order_info = self.exchange.fetchOrder(sl_order, symbol)
            if sl_order_info["status"] == "closed":
                self.exchange.cancelOrder(tp_order, symbol)
                result = "SL"

        return result
    
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
