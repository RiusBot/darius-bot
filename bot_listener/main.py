import json
import parse
import logging
import requests
import asyncio
from config import config
from telethon import TelegramClient, events
from auth import fetch_secret_token_firestore
from collections import Counter


telegram_client = TelegramClient('darius-bot-listener', config["telegram_api_id"], config["telegram_api_hash"])
rose_channel = None
perpetual_channel = None
test_channel = None
sentiment_channel = None
justin_channel = None
whale_channel = None
scalp_channel = None
vegas_channel = None


async def get_channels():
    global test_channel, rose_channel, perpetual_channel, sentiment_channel, justin_channel, whale_channel, scalp_channel, vegas_channel
    logging.info("Get channel")
    test_channel = await telegram_client.get_entity('test')
    rose_channel = await telegram_client.get_entity('🌹 Rose Premium Signal For Bot')
    perpetual_channel = await telegram_client.get_entity('Binance Perpetual Data Pro')
    sentiment_channel = await telegram_client.get_entity('Sentiment Indicator Notification')
    justin_channel = await telegram_client.get_entity('https://t.me/justin_tw')
    whale_channel = await telegram_client.get_entity('whalehunter🐳')
    scalp_channel = await telegram_client.get_entity('Daily Scalping Signal')
    vegas_channel = await telegram_client.get_entity('Vegas 4hr Indicator')
    print(scalp_channel, justin_channel, whale_channel)
    return test_channel, rose_channel, perpetual_channel, sentiment_channel, justin_channel, whale_channel, scalp_channel, vegas_channel


async def get_IDs():
    logging.info("Get IDs")
    async for dialog in telegram_client.iter_dialogs():
        # print(dialog.name, 'has ID', dialog.id)
        pass


async def send_to_execute(info: dict):
    #logging.info("send to execute")
    token = fetch_secret_token_firestore()
    headers = {"Authorization": f"Bearer {token}"}
    
    symbol_list = info["symbol"]
    symbol_list = [] if symbol_list is None else symbol_list
    action = info["action"]
    for symbol in symbol_list:
        info["symbol"] = symbol.strip() if isinstance(symbol, str) else symbol
        logging.info(f"{symbol} {action} send to execute.")
        response = requests.post(config["backend_endpoint"], json=info, headers=headers)
        try:
            logging.info(str(response) + " " + json.dumps(response.json()))
        except Exception:
            logging.info(str(response) + " " + response.text)
        await asyncio.sleep(60)


with telegram_client:
    telegram_client.loop.run_until_complete(get_IDs())
    telegram_client.loop.run_until_complete(get_channels())


# @telegram_client.on(events.NewMessage(from_users=test_channel, forwards=True))
# async def test_handler(event):
#     buy_info = parse.JustinParser("BUY").parse(event)
#     sell_info = parse.JustinParser("SELL").parse(event)

#     buy = Counter(buy_info['symbol'])
#     sell = Counter(sell_info['symbol'])
#     buy_info['symbol'] = [j for i, cnt in (buy - sell).items() for j in [i]*cnt]
#     sell_info['symbol'] = [j for i, cnt in (sell - buy).items() for j in [i]*cnt]

#     logging.info(json.dumps(buy_info, indent=4))
#     #await send_to_execute(buy_info)

#     logging.info(json.dumps(sell_info, indent=4))
#     await send_to_execute(sell_info)


@telegram_client.on(events.NewMessage(from_users=vegas_channel, forwards=False))
async def vegas_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.VegasParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=justin_channel, forwards=False))
async def justin_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    buy_info = parse.JustinParser("BUY").parse(event)
    sell_info = parse.JustinParser("SELL").parse(event)

    buy = Counter(buy_info['symbol'])
    sell = Counter(sell_info['symbol'])
    buy_info['symbol'] = [j for i, cnt in (buy - sell).items() for j in [i]*cnt]
    sell_info['symbol'] = [j for i, cnt in (sell - buy).items() for j in [i]*cnt]

    logging.info(json.dumps(buy_info, indent=4))
    await send_to_execute(buy_info)

    logging.info(json.dumps(sell_info, indent=4))
    await send_to_execute(sell_info)


@telegram_client.on(events.NewMessage(from_users=rose_channel, forwards=False))
async def rose_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.RoseParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=perpetual_channel, forwards=False))
async def perpetual_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.PerpetualParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=whale_channel, forwards=False))
async def whale_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.WhalehunterParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=scalp_channel, forwards=False))
async def scalp_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.ScalpParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


if __name__ == '__main__':
    while True:
        try:
            logging.info("Start listen")
            telegram_client.start()
            telegram_client.run_until_disconnected()
        except Exception:
            logging.exception("")
