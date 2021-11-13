import time
import requests
import hmac
import hashlib
from urllib import parse


class MEXCRestClient():
    
    def __init__(self, api_key: str, api_secret: str):
        self.API_KEY = api_key
        self.SECRET_KEY = api_secret
        self.ROOT_URL = 'https://www.mexc.com'
        self.markets = {i["symbol"]: i for i in self.get_symbols()}
        self.ssss = "_"
        self.name = "mexc"

    def _get_server_time(self, ):
        return int(time.time())


    def _sign(self, method, path, original_params=None):
        params = {
            'api_key': self.API_KEY,
            'req_time': self._get_server_time(),
        }
        if original_params is not None:
            params.update(original_params)
        params_str = '&'.join('{}={}'.format(k, params[k]) for k in sorted(params))
        to_sign = '\n'.join([method, path, params_str])
        params.update({'sign': hmac.new(self.SECRET_KEY.encode(), to_sign.encode(), hashlib.sha256).hexdigest()})
        return params


    def loadMarkets(self, reload=False):
        if reload:
            self.markets = {i["symbol"]: i for i in self.get_symbols()}
        return self.markets
    
    def get_symbols(self, ):
        """marget data"""
        method = 'GET'
        path = '/open/api/v2/market/symbols'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {'api_key': self.API_KEY}
        response = requests.request(method, url, params=params)
        return response.json().get('data')


    def get_rate_limit(self, ):
        """rate limit"""
        method = 'GET'
        path = '/open/api/v2/common/rate_limit'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {'api_key': self.API_KEY}
        response = requests.request(method, url, params=params)
        return response.json()


    def get_timestamp(self, ):
        """get current time"""
        method = 'GET'
        path = '/open/api/v2/common/timestamp'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {'api_key': self.API_KEY}
        response = requests.request(method, url, params=params)
        return response.json()


    def get_ticker(self, symbol):
        """get ticker information"""
        method = 'GET'
        path = '/open/api/v2/market/ticker'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {
            'api_key': self.API_KEY,
            'symbol': symbol,
        }
        response = requests.request(method, url, params=params)
        return response.json()


    def get_depth(self, symbol, depth):
        """获market depth"""
        method = 'GET'
        path = '/open/api/v2/market/depth'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {
            'api_key': self.API_KEY,
            'symbol': symbol,
            'depth': depth,
        }
        response = requests.request(method, url, params=params)
        return response.json()


    def get_deals(self, symbol, limit):
        """get deals records"""
        method = 'GET'
        path = '/open/api/v2/market/deals'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {
            'api_key': self.API_KEY,
            'symbol': symbol,
            'limit': limit,
        }
        response = requests.request(method, url, params=params)
        return response.json()


    def get_kline(self, symbol, interval, since, limit):
        """k-line data"""
        method = 'GET'
        path = '/open/api/v2/market/kline'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = {
            'api_key': self.API_KEY,
            'symbol': symbol,
            'interval': interval,
            "start_time": since,
            "limit": limit
        }
        response = requests.request(method, url, params=params)
        return response.json()
    
    def fetch_ohlcv(self, symbol, timeframe, since=None, limit=None):
        if since > 9933577171:
            since = int(since / 1000)
        klines = self.get_kline(symbol, timeframe, since, limit)
        for k in klines:
            k[2], k[3], k[4] = k[3], k[4], k[2]
        return klines

    def get_account_info(self, ):
        """account information"""
        method = 'GET'
        path = '/open/api/v2/account/info'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = self._sign(method, path)
        response = requests.request(method, url, params=params)
        return response.json()

    def createLimitBuyOrder(self, symbol: str, amount: float, price: float):
        response = self.place_order(symbol, price, amount, "BID", "LIMIT_ORDER")
        if response["code"] != 200:
            raise Exception(str(response["code"]))
            
        order_id = response["data"]
        order = self.query_order(order_id).get('data')[0]
        order["filled"] = order["deal_quantity"]
        order["timestamp"] = order["create_time"]
        return order
    
    def place_order(self, symbol, price, quantity, trade_type, order_type):
        """place order"""
        method = 'POST'
        path = '/open/api/v2/order/place'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = self._sign(method, path)
        data = {
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'trade_type': trade_type,
            'order_type': order_type,
        }
        response = requests.request(method, url, params=params, json=data)
        return response.json()


    def batch_orders(self, orders):
        """batch order"""
        method = 'POST'
        path = '/open/api/v2/order/place_batch'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = self._sign(method, path)
        response = requests.request(method, url, params=params, json=orders)
        return response.json()


    def cancel_order(self, order_id):
        """cancel in batch"""
        origin_trade_no = order_id
        if isinstance(order_id, list):
            origin_trade_no = parse.quote(','.join(order_id))
        method = 'DELETE'
        path = '/open/api/v2/order/cancel'
        url = '{}{}'.format(self.ROOT_URL, path)
        params = self._sign(method, path, original_params={'order_ids': origin_trade_no})
        if isinstance(order_id, list):
            params['order_ids'] = ','.join(order_id)
        response = requests.request(method, url, params=params)
        return response.json()


    def get_open_orders(self, symbol):
        """current orders"""
        method = 'GET'
        path = '/open/api/v2/order/open_orders'
        original_params = {
            'symbol': symbol,
        }
        url = '{}{}'.format(self.ROOT_URL, path)
        params = self._sign(method, path, original_params=original_params)
        response = requests.request(method, url, params=params)
        return response.json()


    def get_all_orders(self, symbol, trade_type):
        """order list"""
        method = 'GET'
        path = '/open/api/v2/order/list'
        original_params = {
            'symbol': symbol,
            'trade_type': trade_type,
        }
        url = '{}{}'.format(self.ROOT_URL, path)
        params = self._sign(method, path, original_params=original_params)
        response = requests.request(method, url, params=params)
        return response.json()


    def query_order(self, order_id):
        """query order"""
        origin_trade_no = order_id
        if isinstance(order_id, list):
            origin_trade_no = parse.quote(','.join(order_id))
        method = 'GET'
        path = '/open/api/v2/order/query'
        url = '{}{}'.format(self.ROOT_URL, path)
        original_params = {
            'order_ids': origin_trade_no,
        }
        params = self._sign(method, path, original_params=original_params)
        if isinstance(order_id, list):
            params['order_ids'] = ','.join(order_id)
        response = requests.request(method, url, params=params)
        return response.json()


    def get_deal_orders(self, symbol):
        """account deal records"""
        method = 'GET'
        path = '/open/api/v2/order/deals'
        url = '{}{}'.format(self.ROOT_URL, path)
        original_params = {
            'symbol': symbol,
        }
        params = self._sign(method, path, original_params=original_params)
        response = requests.request(method, url, params=params)
        return response.json()


    def get_deal_detail(self, order_id):
        """deal detail"""
        method = 'GET'
        path = '/open/api/v2/order/deal_detail'
        url = '{}{}'.format(self.ROOT_URL, path)
        original_params = {
            'order_id': order_id,
        }
        params = self._sign(method, path, original_params=original_params)
        response = requests.request(method, url, params=params)
        return response.json()
