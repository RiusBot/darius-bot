import ccxt
import json
import logging
import datetime
import concurrent.futures
from rob_worker.services.exchange.ftx.ftx_rest_client import FtxRestClient
from rob_worker.services.exchange.mexc.mexc_rest_client import MEXCRestClient




def order_execute(order_info: dict):
    exchange = get_exchange(
        order_info["exchange"],
        order_info["api_key"],
        order_info["api_secret"]
    )



def get_exchange(exchange: str, api_key: str, api_secret: str):
    if exchange == 'binance':
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'apiKey': api_key,
            "secret": api_secret,
            'options': {
                'defaultType': 'spot',
            },
        })
    elif exchange == "ftx":
        exchange = ccxt.ftx({
            'enableRateLimit': True,
            'apiKey': api_key,
            "secret": api_secret,
        })
    elif exchange == "gate":
        exchange = ccxt.gateio({
            'enableRateLimit': True,
            'apiKey': api_key,
            "secret": api_secret,
            'options': {
                'defaultType': 'spot',
            },
        })
    elif exchange == "mexc":
        exchange = MEXCRestClient(api_key, api_secret)
    else:
        raise Exception(f"Exchange {exchange} not supprorted.")
        
    exchange.loadMarkets(True)
    return exchange
        
        
def sell(exchange, order: dict, symbol: str):
    filled = float(order["filled"])
    sell_order = []
    
    if filled > 0 and symbol == "BETA/USDT":
        size = [0.2, 0.16, 0.16, 0.16, 0.16]
        price = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for s, p in zip(size, price):
            amount = filled * s
            sell_order.append(exchange.createLimitSellOrder(symbol, amount, p))
    
    return sell_order
        
        
def rush(exchange: str, symbol: str, amount: float, price: float):
    if exchange == "binance":
        return _rush(exchange, symbol, amount, price)
    elif exchange in ["ftx", "gate", "mexc"]:
        return _rush_parallel(exchange, symbol, amount, price)

    
def get_invalid_symbol_message(exchange: str):
    if exchange == "binance":
        # 'binance {"code":-1121,"msg":"Invalid symbol."}'
        return ["-1121"]
    elif exchange == "ftx":
        # RateLimitExceeded: ftx {"success":false,"error":"No such market"}
        return ["No such market", "Market is disabled"]
    elif exchange == "gate":
        # gateio Invalid currency pair
        return ["Invalid currency"]
    elif exchange == "mexc":
        return ["30001", "30020", "30021"]
    


def get_exceed_rate_limit_message(exchange: str):
    if exchange == "binance":
        # 'binance {"code":-1015,"msg":"Too many orders."}'
        return ["-1015"]
    elif exchange == "ftx":
        # RateLimitExceeded: ftx {"success":false,"error":"Do not send more than 6 orders total per 200ms"}
        return ["200ms", "Please slow down"]
    elif exchange == "gate":
        # ExchangeError: gateio Internal server error
        return ["Internal server error"]
    elif exchange == "mexc":
        return ["429"]

    
def _rush(exchange: str, symbol: str, amount: float, price: float):

    exceed_rate_limit_msg = get_exceed_rate_limit_message(exchange)
    invalid_symbol_msg = get_invalid_symbol_message(exchange)
    exchange = get_exchange(exchange, symbol)
    # now = datetime.datetime.now()
    # end_time = datetime.datetime(now.year, now.month, now.day, now.hour+1, 10)
    
    while True:
        try:
            order = exchange.createLimitBuyOrder(symbol, amount, price)
            return order
        except Exception as e:
            print(e)
            # if any(map(str(e).__contains__, exceed_rate_limit_msg)):
            #     continue
            # elif any(map(str(e).__contains__, invalid_symbol_msg)):
            #     continue
            if datetime.datetime.now() > end_time:
                raise Exception("End time reached.")
            else:
                raise e


def _rush_parallel(exchange: str, symbol: str, amount: float, price: float):
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        
        order_tasks = list()
        for worker in range(10):
            order_task = executor.submit(_rush, exchange, symbol, amount, price)
            order_tasks.append(order_task)
            
        result_list = list()
        error_list = list()
        for task in concurrent.futures.as_completed(order_tasks):
            try:
                result = task.result()
                result_list.append(result)
            except Exception as e:
                error_list.append(str(e))
                
        if result_list:
            return result_list[0]
        else:
            return error_list[0]
