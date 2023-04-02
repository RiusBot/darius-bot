import os
import ccxt
import time
import json
import shutil
import pickle
import logging
import calendar
from typing import Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from freqtrade.commands import Arguments
from freqtrade.exceptions import OperationalException

from bot_optimizer import config
from bot_optimizer.strategies import riusbot_hedge
from bot_optimizer.services.metric import add_metrics_v2
from bot_optimizer.adapters.mysql.utils import create_performance, create_hyperopt, get_hyperopt, get_message, get_channel


def freqtrade_run(sysargv: str):
    arguments = Arguments(sysargv.split(' '))
    args = arguments.get_parsed_arg()
    if 'func' in args:
        args['func'](args)
    else:
        raise Exception("func missing")
    time.sleep(1)


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

    exchange = getattr(ccxt, exchange)({
        "enableRateLimit": True,
        'options': {
            "defaultType": 'future',
            "adjustForTimeDifference": True,
            "verbose": True,
        },
    })
    exchange.loadMarkets()

    pairs = ['BTC/USDT']
    for i in message:
        symbol = f"{i['symbol']}/USDT"
        pairs.append(symbol)

    available_pairs = set(exchange.loadMarkets().keys())
    rm_pairs = set(["OP/USDT", "SPELL/USDT", "CVX/USDT", "LDO/USDT", "INJ/USDT", "1000LUNC/USDT", "LUNA2/USDT", "FOOTBALL/USDT", "STG/USDT", "QNT/USDT", "APT/USDT", "MINA/USDT", "BLUEBIRD/USDT", "FET/USDT", "T/USDT", "RNDR/USDT", "MAGIC/USDT", "HOOK/USDT", "FXS/USDT", "PHB/USDT", "COCOS/USDT", "STX/USDT", "SSV/USDT", "GMX/USDT", "ASTR/USDT", "HIGH/USDT", "ACH/USDT", "AGIX/USDT", "CFX/USDT", "TRU/USDT", "CKB/USDT", "LQTY/USDT", 'BNX/USDT', ])#'ID/USDT', 'ARB/USDT', 'PERP/USDT'
    pairs = list((set(pairs) & available_pairs) - rm_pairs)
    logging.info(f"Pairs {pairs}")
    return message, pairs

        
def freqtrade_init(
    db,
    channel: str,
    exchange: str,
    start_at: datetime,
    end_at: datetime,
    timeframe: str,
    timerange: str,
    params: dict = {},
    rm_pairs: list = None
):
    logging.info("freqtrade init")

    message, pairs = read_message(db, channel, exchange, start_at, end_at)
    if rm_pairs is not None:
        pairs = list(set(pairs) - set(rm_pairs))
    freqtrade_create_userdir()
    freqtrade_create_config(params, message, pairs, channel)
    freqtrade_download_data(exchange, timeframe, timerange)
    shutil.copyfile(riusbot_hedge.__file__, "user_data/strategies/riusbot_hedge.py")


def freqtrade_create_userdir():
    logging.info("create userdir")
    if os.path.isdir("user_data"):
        shutil.rmtree("user_data")
    sysargv = "create-userdir --userdir user_data"
    freqtrade_run(sysargv)
    
    
def freqtrade_create_config(params, message, pairs, channel):
    dry_run_wallet_dict = {
        'VEGAS': 3000,
        'JUSTIN': 2000,
        'ACDC': 500,
        'MOON': 500,
        'PERPETUAL': 3000
    }
    logging.info("create config")
    config_path = os.path.join(config.__path__[0], "default_config_v2.json")
    freqtrade_config = json.load(open(config_path, "r"))
    freqtrade_config["dry_run_wallet"] = dry_run_wallet_dict.get(channel, 1000)
    freqtrade_config["exchange"]["pair_whitelist"] = pairs
    freqtrade_config["riusbot_trades"] = message
    freqtrade_config["riusbot_params"] = params
    with open("config.json", "w") as f:
        json.dump(freqtrade_config, f)


def freqtrade_download_data(exchange: str, timeframe: str, timerange: str):
    for _ in range(3):
        try:
            logging.info(f"download data {timerange}")
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


def freqtrade_hyperopt_v2(db, json_payload: dict):
    logging.info("freqtrade hyperopt")

    exchange = json_payload.get('exchange', 'binance')
    timeframe = json_payload.get('timeframe', '1h')
    days = json_payload.get('days', 90)
    channel_list = json_payload.get('channels', get_channel(db))
    loss_list = json_payload.get('loss', config.Hyperopt_Loss)
    create = json_payload.get('create', True)
    timerange, start_at, end_at = process_hyperopt_timerange(json_payload['timerange'], days)
    output = defaultdict(dict)

    # ignore channel
    ignore_channel = ["WEBHOOK", "AIRFORCE7", "CTA", "SPACEFORCE", "ACDC"]
    channel_list = list(set(channel_list) - set(ignore_channel))

    for channel in channel_list:

        for loss in loss_list:

            try:
                params = {}
                freqtrade_init(db, channel, exchange, start_at, end_at, timeframe, timerange)
                sysargv = f"hyperopt --strategy riusbot_hedge --timeframe {timeframe} --timerange {timerange} --hyperopt-loss {loss} --spaces roi stoploss -e 300"
                freqtrade_run(sysargv)

                with open("user_data/strategies/riusbot_hedge.json", "r") as f:
                    result = json.load(f)
                    params['take_profit'] = result['params']['roi']['0']
                    params['stop_loss'] = -result['params']['stoploss']['stoploss']
                    params['export_time'] = result['export_time']

                logging.info(f"{channel}, {loss}")
                logging.info(json.dumps(params, indent=4))

                if create:
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
            except OperationalException as e:
                if 'no leverage tiers available' in str(e):
                    err_msg = str(e)
                    rm_pairs = [i.strip() for i in err_msg.split(' ', 1)[1].split('got')[0].strip().split(',')]
            except Exception as e:
                if "Insufficient trade message" in str(e) or 'optimized config' in str(e):
                    logging.error(f"{channel} {start_at}-{end_at} {e}")
                else:
                    logging.exception("")
    return output
                     
                     
def retry(func):
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalException as e:
            if 'no leverage tiers available' in str(e):
                err_msg = str(e)
                rm_pairs = [i.strip() for i in err_msg.split(' ', 1)[1].split('got')[0].strip().split(',')]
                kwargs['rm_pairs'] = rm_pairs
                return func(*args, **kwargs)
            else:
                raise
    return wrap


@retry
def _freqtrade_backtest_v2(db, exchange, channel, loss, start_at, end_at, timeframe, timerange, all_time, create, rm_pairs=None):
    backtest_result = None
    hyperopt = get_hyperopt(db, channel, loss, start_at)
    params = json.loads(hyperopt.to_dict()['params'])
    if all_time:
        start_at = datetime.fromtimestamp(0)
        timerange = f'20210101-{end_at.strftime("%Y%m%d")}'
    freqtrade_init(db, channel, exchange, start_at, end_at, timeframe, timerange, params, rm_pairs)

    sysargv = f"backtesting --strategy riusbot_hedge --timeframe {timeframe} --timerange {timerange} --eps"
    freqtrade_run(sysargv)
    with open("user_data/backtest_results/.last_result.json", "r") as f:
        last_result_path = json.load(f)['latest_backtest']
    with open(os.path.join("user_data/backtest_results", last_result_path), "r") as f:
        backtest_result = json.load(f)

    if all_time:
        backtest_result = add_metrics_v2(backtest_result)

    if create:
        create_performance(
            db,
            start_at,
            end_at,
            json.dumps(backtest_result),
            channel,
            hyperopt
        )
    return backtest_result


def freqtrade_backtest_v2(db, json_payload: dict):
    logging.info("freqtrade backtest")

    exchange = json_payload.get('exchange', 'binance')
    timeframe = json_payload.get('timeframe', '1h')
    timerange, start_at, end_at = process_backtest_timerange(json_payload['timerange'])
    channel_list = json_payload.get('channels', get_channel(db))
    loss_list = json_payload.get('loss', ["SharpeHyperOptLoss"])
    create = json_payload.get('create', True)
    all_time = json_payload.get('all_time', False)
    output = defaultdict(dict)

    # ignore channel
    ignore_channel = ["WEBHOOK"]
    channel_list = list(set(channel_list) - set(ignore_channel))

    # remove hyperopt params file
    if os.path.isfile("user_data/strategies/riusbot_hedge.json"):
        os.remove("user_data/strategies/riusbot_hedge.json")

    for channel in channel_list:
        for loss in loss_list:  # config.Hyperopt_Loss:
            try:
                backtest_result = _freqtrade_backtest_v2(db, exchange, channel, loss, start_at, end_at, timeframe, timerange, all_time, create)
                output[channel][loss] = backtest_result
            except Exception as e:
                if "Insufficient trade message" in str(e) or 'optimized config' in str(e):
                    logging.error(f"{channel} {start_at}-{end_at} {e}")
                else:
                    logging.exception("")

    return output
    