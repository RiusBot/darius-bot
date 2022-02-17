import os
import json
import shutil
import pickle
import logging
from typing import Any, List
from datetime import datetime, timedelta
from freqtrade.commands import Arguments

from bot_optimizer import config
from bot_optimizer.strategies import riusbot
from bot_optimizer.adapters.mysql.utils import create_performance, create_hyperopt, get_hyperopt


logging.getLogger('freqtrade').setLevel(logging.ERROR)


def freqtrade_run(sysargv: str):
    arguments = Arguments(sysargv.split(' '))
    args = arguments.get_parsed_arg()
    if 'func' in args:
        args['func'](args)
    else:
        raise Exception("func missing")


def freqtrade_init(json_payload, params={}):
    logging.info("freqtrade init")
    freqtrade_create_userdir()
    freqtrade_create_config(json_payload, params)
    freqtrade_download_data(json_payload)
    shutil.copyfile(riusbot.__file__, "user_data/strategies/riusbot.py")


def freqtrade_create_userdir():
    logging.info("create userdir")
    sysargv = "create-userdir --userdir user_data"
    freqtrade_run(sysargv)
    
    
def freqtrade_create_config(json_payload, params):
    logging.info("create config")
    config_path = os.path.join(config.__path__[0], "default_config.json")
    freqtrade_config = json.load(open(config_path, "r"))
    pairs = list(set([f"{i['symbol']}/USDT" for i in json_payload['message']]))
    freqtrade_config["exchange"]["pair_whitelist"] = pairs
    freqtrade_config["riusbot_trades"] = json_payload['message']
    freqtrade_config["riusbot_params"] = params
    with open("config.json", "w") as f:
        json.dump(freqtrade_config, f)


def freqtrade_download_data(json_payload):
    logging.info("download data")
    exchange = json_payload.get('exchange', 'binance')
    timeframe = json_payload.get('timeframe', '1h')
    timerange = json_payload.get('timerange', (datetime.now() - timedelta(days=7)).strftime('%Y%m%d-'))

    sysargv = f"download-data --exchange {exchange} --timeframe {timeframe} --timerange {timerange}"
    freqtrade_run(sysargv)


def freqtrade_hyperopt(db, json_payload: dict):
    logging.info("freqtrade hyperopt")
    freqtrade_init(json_payload)

    timeframe = json_payload.get('timeframe', '1h')
    days = json_payload.get('days', '180')
    timerange = json_payload.get('timerange', (datetime.now() - timedelta(days=days)).strftime('%Y%m%d-'))
    loss = json_payload.get('loss')
    sysargv = f"hyperopt --strategy riusbot --timeframe {timeframe} --timerange {timerange} --hyperopt-loss {loss} --spaces roi stoploss"
    freqtrade_run(sysargv)
    
    with open("user_data/strategies/riusbot.json", "r") as f:
        result = json.load(f)
        params = {
            'take_profit': result['params']['roi']['0'],
            'stop_loss': -result['params']['stoploss']['stoploss'],
            'export_time': result['export_time']
        }
        print(json.dumps(params, indent=4))

    create_hyperopt(
        db,
        json.dumps(params),
        json_payload.get('channel'),
        days,
        loss
    )


def freqtrade_backtest(db, json_payload: dict):
    logging.info("freqtrade backtest")

    channel = json_payload.get('channel')
    params = get_hyperopt(channel, 'OnlyProfitHyperOptLoss')
    freqtrade_init(json_payload, params)

    timeframe = json_payload.get('timeframe', '1h')
    days = {'day': 1, 'week': 7, 'month': 30}.get(json_payload.get('breakdown'))
    timerange = json_payload.get('timerange', (datetime.now() - timedelta(days=days)).strftime('%Y%m%d-'))
    sysargv = f"backtesting --strategy riusbot --timeframe {timeframe} --timerange {timerange} --export trades"
    freqtrade_run(sysargv)

    with open("user_data/backtest_results/.last_result.json", "r") as f:
        last_result_path = json.load(f)['latest_backtest']
    with open(os.path.join("user_data/backtest_results", last_result_path), "r") as f:
        backtest_result = json.load(f)
    
    create_performance(
        db,
        timerange[:-1],
        breakdown,
        json.dumps(backtest_result),
        channel,
        hyper_id
    )
    
    