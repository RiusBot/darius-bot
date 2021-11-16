import json
import logging
from bot_executor.services.exchange.ftx import FtxClient
from bot_executor.services.exchange.binance import BinanceClient


def order_execute(order_info: dict):
    logging.info("Start order execute")
    exchange = get_exchange(order_info)
    order = exchange.make_order(order_info)
    if order:
        tp_order, sl_order = exchange.make_oco_order(order, order_info)
    return {
        "open": order,
        "sl": sl_order,
        "tp": tp_order,
    }


def get_exchange(order_info: dict):
    exchange = order_info["exchange"]
    if exchange == 'binance':
        exchange = BinanceClient(order_info)
    elif exchange == "ftx":
        exchange = FtxClient(order_info)
    # elif exchange == "gate":
    #     pass
    # elif exchange == "mexc":
    #     pass
    else:
        raise Exception(f"Exchange {exchange} not supprorted.")
    return exchange
