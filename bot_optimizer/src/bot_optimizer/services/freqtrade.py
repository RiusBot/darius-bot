import os
import ccxt
import json
import shutil
import pickle
import logging
import calendar
from typing import Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from freqtrade.commands import Arguments

from bot_optimizer import config
from bot_optimizer.strategies import riusbot, riusbot_sell
from bot_optimizer.adapters.mysql.utils import create_performance, create_hyperopt, get_hyperopt, get_message, get_channel


def freqtrade_run(sysargv: str):
    arguments = Arguments(sysargv.split(' '))
    args = arguments.get_parsed_arg()
    if 'func' in args:
        args['func'](args)
    else:
        raise Exception("func missing")


def read_message(
    db,
    channel: str,
    exchange: str,
    start_at: datetime,
    end_at: datetime
):
    message = get_message(db, channel, start_at, end_at)
    if not message:
        raise Exception("Insufficient trade message")

    exchange = getattr(ccxt, exchange)({})
    exchange.loadMarkets()

    pairs = []
    for i in message:
        symbol = f"{i['symbol']}/USDT"
        if symbol in exchange.markets:
            pairs.append(symbol)

    pairs = list(set(pairs))
    return message, pairs

        
def freqtrade_init(
    db,
    channel: str,
    exchange: str,
    start_at: datetime,
    end_at: datetime,
    timeframe: str,
    timerange: str,
    params: dict = {}
):
    logging.info("freqtrade init")
    
    message, pairs = read_message(db, channel, exchange, start_at, end_at)
    freqtrade_create_userdir()
    freqtrade_create_config(params, message, pairs)
    freqtrade_download_data(exchange, timeframe, timerange)
    shutil.copyfile(riusbot.__file__, "user_data/strategies/riusbot.py")
    shutil.copyfile(riusbot_sell.__file__, "user_data/strategies/riusbot_sell.py")


def freqtrade_create_userdir():
    logging.info("create userdir")
    if os.path.isdir("user_data"):
        shutil.rmtree("user_data")
    sysargv = "create-userdir --userdir user_data"
    freqtrade_run(sysargv)
    
    
def freqtrade_create_config(params, message, pairs):
    logging.info("create config")
    config_path = os.path.join(config.__path__[0], "default_config.json")
    freqtrade_config = json.load(open(config_path, "r"))
    freqtrade_config["exchange"]["pair_whitelist"] = pairs
    freqtrade_config["riusbot_trades"] = message
    freqtrade_config["riusbot_params"] = params
    with open("config.json", "w") as f:
        json.dump(freqtrade_config, f)


def freqtrade_download_data(exchange: str, timeframe: str, timerange: str):
    for _ in range(3):
        try:
            logging.info("download data")
            sysargv = f"download-data --exchange {exchange} --timeframe {timeframe} --timerange {timerange}"
            freqtrade_run(sysargv)
            return
        except Exception as e:
            logging.error(f"download data failed. {e}")
            logging.info(f"Retry {_}")


def process_hyperopt_timerange(timerange: str, days: int):
    start_at, end_at = timerange.split('-')
    end_at = datetime.strptime(end_at, "%Y%m%d") if end_at else datetime.now()
    start_at = datetime.strptime(start_at, "%Y%m%d") if start_at else end_at - timedelta(days=days)
    return timerange, start_at, end_at


def process_backtest_timerange(timerange: str):
    now = datetime.now()
    y, m, d = now.year, now.month, now.day
    _, last_day = calendar.monthrange(y, m)
    start_at, end_at = timerange.split('-')
    end_at = datetime.strptime(end_at, "%Y%m%d") if end_at else datetime(y, m, last_day)
    start_at = datetime.strptime(start_at, "%Y%m%d") if start_at else datetime(y, m, 1)
    return timerange, start_at, end_at


def freqtrade_hyperopt(db, json_payload: dict):
    logging.info("freqtrade hyperopt")
    
    exchange = json_payload.get('exchange', 'binance')
    timeframe = json_payload.get('timeframe', '1h')
    days = json_payload.get('days', '90')
    timerange, start_at, end_at = process_hyperopt_timerange(json_payload['timerange'], days)
    output = defaultdict(dict)

    for channel in get_channel(db):

        for loss in config.Hyperopt_Loss:

            try:
                params = {
                    'take_profit': 0,
                    'stop_loss': 0,
                    'export_time': None,
                }

                freqtrade_init(db, channel, exchange, start_at, end_at, timeframe, timerange)
                sysargv = f"hyperopt --strategy riusbot --timeframe {timeframe} --timerange {timerange} --hyperopt-loss {loss} --spaces roi stoploss -e 20"
                freqtrade_run(sysargv)

                with open("user_data/strategies/riusbot.json", "r") as f:
                    result = json.load(f)
                    params['take_profit'] += result['params']['roi']['0']
                    params['stop_loss'] += -result['params']['stoploss']['stoploss']
                    params['export_time'] = result['export_time']

                try:
                    sysargv = f"hyperopt --strategy riusbot_sell --timeframe {timeframe} --timerange {timerange} --hyperopt-loss {loss} --spaces roi stoploss -e 20"
                    freqtrade_run(sysargv)

                    with open("user_data/strategies/riusbot_sell.json", "r") as f:
                        result = json.load(f)
                        params['take_profit'] += -result['params']['stoploss']['stoploss']
                        params['stop_loss'] += result['params']['roi']['0']
                        params['export_time'] = result['export_time']

                    params['take_profit'] /= 2
                    params['stop_loss'] /= 2
                except:
                    logging.exception("")

                logging.info(f"{channel}, {loss}")
                logging.info(json.dumps(params, indent=4))

                create_hyperopt(
                    db,
                    json.dumps(params),
                    channel,
                    days,
                    loss,
                    start_at,
                    end_at
                )
                output[channel][loss] = params
            except Exception as e:
                if "Insufficient trade message" in str(e) or 'optimized config' in str(e):
                    logging.error(f"{channel} {start_at}-{end_at} {e}")
                else:
                    logging.exception("")
    return output


def freqtrade_backtest(db, json_payload: dict):
    logging.info("freqtrade backtest")

    exchange = json_payload.get('exchange', 'binance')
    timeframe = json_payload.get('timeframe', '1h')
    timerange, start_at, end_at = process_backtest_timerange(json_payload['timerange'])
    output = defaultdict(dict)
    
    # remove hyperopt params file
    if os.path.isfile("user_data/strategies/riusbot.json"):
        os.remove("user_data/strategies/riusbot.json")
    if os.path.isfile("user_data/strategies/riusbot_sell.json"):
        os.remove("user_data/strategies/riusbot_sell.json")
    
    for channel in get_channel(db):

        for loss in ["SharpeHyperOptLoss"]:  # config.Hyperopt_Loss:

            try:
                backtest_result = None
                hyperopt = get_hyperopt(db, channel, loss, start_at)
                params = json.loads(hyperopt.to_dict()['params'])
                freqtrade_init(db, channel, exchange, start_at, end_at, timeframe, timerange, params)

                sysargv = f"backtesting --strategy-list riusbot riusbot_sell --timeframe {timeframe} --timerange {timerange}"
                freqtrade_run(sysargv)
                with open("user_data/backtest_results/.last_result.json", "r") as f:
                    last_result_path = json.load(f)['latest_backtest']
                with open(os.path.join("user_data/backtest_results", last_result_path), "r") as f:
                    backtest_result = json.load(f)

                create_performance(
                    db,
                    start_at,
                    end_at,
                    json.dumps(backtest_result),
                    channel,
                    hyperopt
                )
                output[channel][loss] = backtest_result

            except Exception as e:
                if "Insufficient trade message" in str(e) or 'optimized config' in str(e):
                    logging.error(f"{channel} {start_at}-{end_at} {e}")
                else:
                    logging.exception("")

    return output
    