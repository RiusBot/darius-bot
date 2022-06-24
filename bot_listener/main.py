import os
import json
import parse
import logging
import requests
import asyncio
from config import config
from datetime import datetime
from telethon import TelegramClient, events
from auth import fetch_secret_token_firestore
from collections import Counter
from json.decoder import JSONDecodeError


telegram_client = TelegramClient('darius-bot-listener', config["telegram_api_id"], config["telegram_api_hash"])
rose_channel = None
perpetual_channel = None
test_channel = None
sentiment_channel = None
justin_channel = None
whale_channel = None
scalp_channel = None
vegas_channel = None
courage_channel = None
moon_channel = None
acdc_channel = None
airforce_channel = None
cta_channel = None
logging.info(config["backend_endpoint"])


async def get_channels():
    global test_channel, rose_channel, perpetual_channel, sentiment_channel, justin_channel, whale_channel, scalp_channel, vegas_channel, courage_channel, moon_channel, acdc_channel, airforce_channel, cta_channel

    logging.info("Get channel")
    test_channel = await telegram_client.get_entity('test')
    rose_channel = await telegram_client.get_entity('🌹 Rose Premium Signal For Bot')
    perpetual_channel = await telegram_client.get_entity('Binance Perpetual Data Pro')
    sentiment_channel = await telegram_client.get_entity('Sentiment Indicator Notification')
    justin_channel = await telegram_client.get_entity('https://t.me/justin_tw')
    whale_channel = await telegram_client.get_entity('whalehunter🐳')
    scalp_channel = await telegram_client.get_entity('Daily Scalping Signal')
    vegas_channel = await telegram_client.get_entity('Vegas 4hr Indicator')
    courage_channel = await telegram_client.get_entity('Cryptophet Trading Room')
    moon_channel = await telegram_client.get_entity('Moon Indicator')
    acdc_channel = await telegram_client.get_entity('✈️ACDC策略快訊✈️')
    airforce_channel = await telegram_client.get_entity('空軍司令部(F)')
    cta_channel = await telegram_client.get_entity('CTA Strategy')

    for i in [vegas_channel, courage_channel, perpetual_channel, moon_channel, acdc_channel, airforce_channel, cta_channel]:
        print(i)
        print()

    await telegram_client.send_message(entity=test_channel, message='start listener')

    return test_channel, rose_channel, perpetual_channel, sentiment_channel, justin_channel, whale_channel, scalp_channel, vegas_channel, courage_channel, moon_channel, acdc_channel, airforce_channel, cta_channel


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
    quantity_list = info["quantity"]
    symbol_list = [] if symbol_list is None else symbol_list
    quantity_list = [] if quantity_list is None else quantity_list
    action = info["action"]
    for symbol, quantity in zip(symbol_list, quantity_list):
        info["symbol"] = symbol.strip() if isinstance(symbol, str) else symbol
        info["quantity"] = quantity
        logging.info(f"{symbol} {action} send to execute.")

        for endpoint in config["backend_endpoint"]:
            logging.info(f"{endpoint}")
            response = requests.post(endpoint, json=info, headers=headers)
            try:
                logging.info(str(response) + " " + json.dumps(response.json()))
            except Exception:
                logging.info(str(response) + " " + response.text)
            break
        
        await asyncio.sleep(5)
        
    logging.info("complete execute")


with telegram_client:
    telegram_client.loop.run_until_complete(get_IDs())
    telegram_client.loop.run_until_complete(get_channels())


@telegram_client.on(events.NewMessage())
async def handler(event):
    if event.chat is not None and hasattr(event.chat, "title"):
        if "Cryptophet Trading Room" in event.chat.title:
            try:
                if isinstance(json.loads(event.text), dict):
                    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
                    info = parse.CourageParser().parse(event)
                    logging.info(json.dumps(info, indent=4))
                    await send_to_execute(info)
            except JSONDecodeError:
                pass
            except Exception:
                logging.exception("")
        elif "✈️ACDC策略快訊✈️" in event.chat.title:
            try:
                # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
                info = parse.ACDCParser().parse(event)
                logging.info(json.dumps(info, indent=4))
                await send_to_execute(info)
            except Exception:
                logging.exception("")
        elif "空軍司令部(F)" in event.chat.title:
            try:
                # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
                info = parse.AirforceParser().parse(event)
                logging.info(json.dumps(info, indent=4))
                await send_to_execute(info)
            except Exception:
                logging.exception("")


# @telegram_client.on(events.NewMessage(from_users=test_channel, forwards=False))
# async def test_handler(event):
#     logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
#     try:
#         json.loads(event.text)
#         info = parse.CourageParser().parse(event)
#         logging.info(json.dumps(info, indent=4))
#         # await send_to_execute(info)
#     except Exception:
#         pass


# @telegram_client.on(events.NewMessage(from_users=acdc_channel, forwards=True))
# async def acdc_handler(event):
#     logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
#     info = parse.ACDCParser().parse(event)
#     logging.info(json.dumps(info, indent=4))
#     await send_to_execute(info)

# @telegram_client.on(events.NewMessage(from_users=airforce_channel, forwards=True))
# async def airforce_handler(event):
#     logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
#     info = parse.AirforceParser().parse(event)
#     logging.info(json.dumps(info, indent=4))
#     await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=moon_channel, forwards=False))
async def moon_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.MoonParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=vegas_channel, forwards=False))
async def vegas_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.VegasParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=cta_channel, forwards=False))
async def cta_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")

    info = json.loads(event.text)
    info = {symbol: float(amount) for symbol, amount in info.items()}

    busd_state_file = "./cta_state/busd_state"
    usdt_state_file = "./cta_state/usdt_state"
    if "BUSD" in list(info.keys())[0]:
        quote = "BUSD"
    elif "USDT" in list(info.keys())[0]:
        quote = "USDT"

    def write_state(info: dict):
        if quote == "BUSD":
            state_file = busd_state_file
        elif quote == "USDT":
            state_file = usdt_state_file

        logging.info(f"write state file {state_file}")
        with open(f"{state_file}.json", "w") as f:
            json.dump(info, f)
        with open(f"{state_file}_{int(datetime.now().timestamp())}.json", "w") as f:
            json.dump(info, f)

    def read_state(state_file: str):
        state = {}
        if os.path.isfile(f"{state_file}.json"):
            logging.info("load state")
            with open(f"{state_file}.json", "r") as f:
                state = json.load(f)
        return state

    usdt_state = read_state(usdt_state_file)
    busd_state = read_state(busd_state_file)

    buy_info = parse.CtaParser("BUY", usdt_state, busd_state, quote).parse(event)
    sell_info = parse.CtaParser("SELL", usdt_state, busd_state, quote).parse(event)

    logging.info(json.dumps(buy_info, indent=4))
    await send_to_execute(buy_info)

    logging.info(json.dumps(sell_info, indent=4))
    await send_to_execute(sell_info)

    write_state(info)


@telegram_client.on(events.NewMessage(from_users=justin_channel, forwards=False))
async def justin_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
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
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.RoseParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=perpetual_channel, forwards=False))
async def perpetual_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.PerpetualParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=courage_channel, forwards=False))
async def courage_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    try:
        if isinstance(json.loads(event.text), dict):
            info = parse.CourageParser().parse(event)
            logging.info(json.dumps(info, indent=4))
            await send_to_execute(info)
    except Exception:
        logging.exception("")


@telegram_client.on(events.NewMessage(from_users=whale_channel, forwards=False))
async def whale_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.WhalehunterParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=scalp_channel, forwards=False))
async def scalp_handler(event):
    # logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
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
