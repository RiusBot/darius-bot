import json
import logging
from bot_executor.services.exchange.ftx import FtxClient
from bot_executor.services.exchange.ftxus import FtxusClient
from bot_executor.services.exchange.binance import BinanceClient


def order_execute(order_info: dict):
    logging.info("Start order execute")
    exchange = get_exchange(order_info)
    order = exchange.make_order(order_info)
    tp_order, sl_orer = None, None
    if order:
        tp_order, sl_order = exchange.make_oco_order(order, order_info)

    result = {
        "status": "error" if order is None else "success",
        "open_order": order.get("id", order.get("info", {}).get("id")),
        "sl_order": None if sl_order is None else sl_order.get("id", sl_order.get("info", {}).get("id")),
        "tp_order": None if tp_order is None else tp_order.get("id", tp_order.get("info", {}).get("id")),
        "price": order.get("average", order.get("price"))
    }
    logging.info("Results:")
    logging.info(json.dumps(result, indent=4))
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
