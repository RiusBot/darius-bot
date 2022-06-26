import logging
import numpy as np
from datetime import datetime, timedelta


def calcuate_roi(result: dict):
    buy_profit = result['strategy']['riusbot']['final_balance'] - 1000
    sell_profit = 1000 - result['strategy']['riusbot_sell']['final_balance']
    profit = buy_profit + sell_profit
    roi = profit / 1000 * 100
    
    buy_daily_profit = result['strategy']['riusbot']['daily_profit']
    sell_daily_profit = result['strategy']['riusbot_sell']['daily_profit']
    start_date = datetime.strptime(min(buy_daily_profit[0][0], sell_daily_profit[0][0]), '%Y-%m-%d')
    end_date = datetime.strptime(min(buy_daily_profit[-1][0], sell_daily_profit[-1][0]), '%Y-%m-%d')
    days = (end_date - start_date) / timedelta(days=1)
    
    annual_roi = (1 + (profit / 1000)) ** (1 / (days/365) - 1)
    return roi, annual_roi


def calculate_sharperatio(result: dict):
    buy_daily_profit = result['strategy']['riusbot']['daily_profit']
    sell_daily_profit = result['strategy']['riusbot_sell']['daily_profit']
    start_date = datetime.strptime(min(buy_daily_profit[0][0], sell_daily_profit[0][0]), '%Y-%m-%d')
    end_date = datetime.strptime(min(buy_daily_profit[-1][0], sell_daily_profit[-1][0]), '%Y-%m-%d')
    
    buy_daily_profit = {i[0]: float(i[1]) for i in buy_daily_profit}
    sell_daily_profit = {i[0]: -float(i[1]) for i in sell_daily_profit}
    
    daily_profit = [0]
    daily_date = []
    while (start_date <= end_date):
        date = start_date.strftime("%Y-%m-%d")
        profit = buy_daily_profit.get(date, 0) + sell_daily_profit.get(date, 0)
        daily_profit.append(profit)
        daily_date.append(date)
        start_date += timedelta(days=1)

    daily_balance = np.cumsum(daily_profit) + 1000
    tmp = (daily_balance[1:] - daily_balance[:-1]) / daily_balance[:-1]
    sharpratio = (np.mean(tmp) - 0.0001) / np.std(tmp) * np.sqrt(252)
    return sharpratio

# calculate_sharperatio(result, 'COURAGE'), calcuate_roi(result, 'COURAGE')


def calcuate_roi_v2(result: dict):
    report = result['strategy']['riusbot_hedge']
    roi = report['profit_total']
    days = report['backtest_days']
    annual_roi = ((1 + roi) ** (1 / (days/365)) - 1)
    return roi, annual_roi


def calculate_sharperatio_v2(result: dict):
    report = result['strategy']['riusbot_hedge']
    daily_profit = [0] + [i[1] for i in report['daily_profit']]
    daily_balance = np.cumsum(daily_profit) + report['starting_balance']
    tmp = (daily_balance[1:] - daily_balance[:-1]) / daily_balance[:-1]
    sharpratio = (np.mean(tmp) - 0.0001) / np.std(tmp) * np.sqrt(252)
    return sharpratio


def add_metrics_v2(backtest_report: dict):
    additional_metric = {
        'annual_roi': calcuate_roi_v2(backtest_report)[1],
        'sharperatio': calculate_sharperatio_v2(backtest_report),
    }
    logging.info(f"additional metric {additional_metric}")
    backtest_report['strategy']['riusbot_hedge'].update(additional_metric)
    return backtest_report
    

def add_metrics(backtest_report: dict):
    additional_metric = {
        'annual_roi': calcuate_roi(backtest_report)[1],
        'sharperatio': calculate_sharperatio(backtest_report),
    }
    logging.info(f"additional metric {additional_metric}")
    backtest_report['strategy']['riusbot'].update(additional_metric)
    backtest_report['strategy']['riusbot_sell'].update(additional_metric)
    return backtest_report
