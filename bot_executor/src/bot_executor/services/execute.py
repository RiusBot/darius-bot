import json
import logging
from bot_executor.services.exchange.ftx import FtxClient
from bot_executor.services.exchange.ftxus import FtxusClient
from bot_executor.services.exchange.binance import BinanceClient


def order_execute(order_info: dict):
    logging.debug("Start order execute")
    exchange = get_exchange(order_info)
    order = exchange.make_order(order_info)
    if order and isinstance(order, str):
        # encountered error
        err_msg = order
        return {"error_message": err_msg}
    
    
    tp_order, sl_orer = None, None
    if order and isinstance(order, dict):
        tp_order, sl_order = exchange.make_oco_order(order, order_info)

    result = {
        "status": 'success' if order else 'error',
        "open_order": order.get("id", order.get("info", {}).get("id")),
        "sl_order": None if sl_order is None else sl_order.get("id", sl_order.get("info", {}).get("id")),
        "tp_order": None if tp_order is None else tp_order.get("id", tp_order.get("info", {}).get("id")),
        "price": order.get("average", order.get("price"))
    }
    logging.debug(f"Results: {result}")
    return result


def get_exchange(order_info: dict):
    exchange = order_info["exchange"]
    if exchange == 'binance':
        exchange = BinanceClient(order_info)
    elif exchange == "ftx":
        exchange = FtxClient(order_info)
    elif exchange == "ftxus":
        exchange = FtxusClient(order_info)
    # elif exchange == "gate":
    #     pass
    # elif exchange == "mexc":
    #     pass
    else:
        raise Exception(f"Exchange {exchange} not supprorted.")
    return exchange


def order_clean(order_info: dict):
    exchange = get_exchange(order_info)
    if order_info["type"] == "limit":
        logging.debug(f"Start limit order clean for trade {order_info['trade_id']}")
        exchange = get_exchange(order_info)
        status = exchange.clean_limit_order(
            order_info["open_order"],
            order_info["symbol"]
        )
        result = {"status": status}
    elif order_info["type"] == "oco":
        logging.debug(f"Start oco order clean for trade {order_info['trade_id']}")
        exchange = get_exchange(order_info)
        status = exchange.clean_oco_order(
            order_info["sl_order"],
            order_info["tp_order"],
            order_info["symbol"]
        )
        result = {"status": status}
    else:
        raise Exception(f"Clean order type {order_info['type']} not supported")

    logging.debug(f"Results: {result['status']}")
    return result
