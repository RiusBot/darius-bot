def calcuate_roi(result: dict, channel: str):
    buy_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot']['final_balance'] - 1000
    sell_profit = 1000 - result[channel]['SharpeHyperOptLoss']['strategy']['riusbot_sell']['final_balance']
    profit = buy_profit + sell_profit
    roi = profit / 1000 * 100
    
    buy_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot']['daily_profit']
    sell_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot_sell']['daily_profit']
    start_date = datetime.strptime(min(buy_daily_profit[0][0], sell_daily_profit[0][0]), '%Y-%m-%d')
    end_date = datetime.strptime(min(buy_daily_profit[-1][0], sell_daily_profit[-1][0]), '%Y-%m-%d')
    days = (start_date - end_date) / timedelta(days=1)
    
    annual_roi = (1 + (profit / 1000)) ** (1 / (days/365)) * 100
    
    return roi, annual_roi


def calculate_sharperatio(result: dict, channel: str):
    if channel not in result:
        raise Exception(f"{channel} not in result")
    
    buy_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot']['daily_profit']
    sell_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot_sell']['daily_profit']
    start_date = datetime.strptime(min(buy_daily_profit[0][0], sell_daily_profit[0][0]), '%Y-%m-%d')
    end_date = datetime.strptime(min(buy_daily_profit[-1][0], sell_daily_profit[-1][0]), '%Y-%m-%d')
    
    buy_daily_profit = {i[0]: float(i[1]) for i in buy_daily_profit}
    sell_daily_profit = {i[0]: -float(i[1]) for i in sell_daily_profit}
    
    daily_profit = []
    daily_date = []
    while (start_date < end_date):
        date = start_date.strftime("%Y-%m-%d")
        profit = buy_daily_profit.get(date, 0) + sell_daily_profit.get(date, 0)
        daily_profit.append(profit)
        daily_date.append(date)
        start_date += timedelta(days=1)
        
    daily_balance = np.cumsum(daily_profit) + 1000
    tmp = []
    for i in range(1, len(daily_balance)):
        tmp.append((daily_balance[i] - daily_balance[i-1]) / daily_balance[i-1])

    sharpratio = (np.mean(tmp) - 0.0002) / np.std(tmp) * np.sqrt(252)
    return sharpratio

# calculate_sharperatio(result, 'COURAGE'), calcuate_roi(result, 'COURAGE')


def calcuate_roi_v2(result: dict, channel: str):
    buy_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot']['final_balance'] - 1000
    sell_profit = 1000 - result[channel]['SharpeHyperOptLoss']['strategy']['riusbot_sell']['final_balance']
    profit = buy_profit + sell_profit
    roi = profit / 1000 * 100
    
    buy_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot']['daily_profit']
    sell_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot_sell']['daily_profit']
    start_date = datetime.strptime(min(buy_daily_profit[0][0], sell_daily_profit[0][0]), '%Y-%m-%d')
    end_date = datetime.strptime(min(buy_daily_profit[-1][0], sell_daily_profit[-1][0]), '%Y-%m-%d')
    days = (start_date - end_date) / timedelta(days=1)
    
    annual_roi = (1 + (profit / 1000)) ** (1 / (days/365)) * 100
    
    return roi, annual_roi


def calculate_sharperatio_v2(result: dict, channel: str):
    if channel not in result:
        raise Exception(f"{channel} not in result")
    
    buy_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot']['daily_profit']
    sell_daily_profit = result[channel]['SharpeHyperOptLoss']['strategy']['riusbot_sell']['daily_profit']
    start_date = datetime.strptime(min(buy_daily_profit[0][0], sell_daily_profit[0][0]), '%Y-%m-%d')
    end_date = datetime.strptime(min(buy_daily_profit[-1][0], sell_daily_profit[-1][0]), '%Y-%m-%d')
    
    buy_daily_profit = {i[0]: float(i[1]) for i in buy_daily_profit}
    sell_daily_profit = {i[0]: -float(i[1]) for i in sell_daily_profit}
    
    daily_profit = []
    daily_date = []
    while (start_date < end_date):
        date = start_date.strftime("%Y-%m-%d")
        profit = buy_daily_profit.get(date, 0) + sell_daily_profit.get(date, 0)
        daily_profit.append(profit)
        daily_date.append(date)
        start_date += timedelta(days=1)
        
    daily_balance = np.cumsum(daily_profit) + 1000
    tmp = []
    for i in range(1, len(daily_balance)):
        tmp.append((daily_balance[i] - daily_balance[i-1]) / daily_balance[i-1])

    sharpratio = (np.mean(tmp) - 0.0002) / np.std(tmp) * np.sqrt(252)
    return sharpratio
