import json
import parse
import logging
import requests
# import asyncio
from config import config
from telethon import TelegramClient, events


telegram_client = TelegramClient('darius-bot-listener', config["telegram_api_id"], config["telegram_api_hash"])
rose_channel = None
perpetual_channel = None
test_channel = None
sentiment_channel = None
justin_channel = None
whale_channel = None


async def get_channels():
    global test_channel, rose_channel, perpetual_channel, sentiment_channel, justin_channel, whale_channel
    logging.info("Get channel")
    test_channel = await telegram_client.get_entity('test')
    rose_channel = await telegram_client.get_entity('🌹 Rose Premium Signal For Bot')
    perpetual_channel = await telegram_client.get_entity('Binance Perpetual Data Pro')
    sentiment_channel = await telegram_client.get_entity('Sentiment Indicator Notification')
    justin_channel = await telegram_client.get_entity('https://t.me/justin_tw')
    whale_channel = await telegram_client.get_entity('whalehunter')
    return test_channel, rose_channel, perpetual_channel, sentiment_channel, justin_channel, whale_channel


async def get_IDs():
    logging.info("Get IDs")
    async for dialog in telegram_client.iter_dialogs():
        # print(dialog.name, 'has ID', dialog.id)
        pass


async def send_to_execute(info: dict):
    logging.info("send to execute")
    response = requests.post(config["execute_endpoint"], json=info)
    logging.info(str(response))
    try:
        logging.info(json.dumps(response.json()))
    except Exception:
        logging.info(response.text)


with telegram_client:
    telegram_client.loop.run_until_complete(get_IDs())
    telegram_client.loop.run_until_complete(get_channels())


@telegram_client.on(events.NewMessage(from_users=test_channel, forwards=False))
async def test_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.RoseParser().parse(event)
    logging.info(json.dumps(info, indent=4))


@telegram_client.on(events.NewMessage(from_users=rose_channel, forwards=False))
async def rose_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.RoseParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    # await send_to_execute(info)


@telegram_client.on(events.NewMessage(from_users=perpetual_channel, forwards=False))
async def perpetual_handler(event):
    logging.info(f"Received message from {event.chat.title}\n{event.text}\n")
    info = parse.PerpetualParser().parse(event)
    logging.info(json.dumps(info, indent=4))
    # await send_to_execute(info)


if __name__ == '__main__':
    while True:
        try:
            logging.info("Start listen")
            telegram_client.start()
            telegram_client.run_until_disconnected()
        except Exception:
            logging.exception("")
