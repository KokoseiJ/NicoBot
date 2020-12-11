from discordapi.client import DiscordClient
import logging
import time

logger = logging.getLogger("NicoBot")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

ch.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logger.addHandler(ch)

with open("token") as f:
    client = DiscordClient(f.read())

client.gateway.connect()

try:
    for event, data in client.event_handler.event_generator():
        print(event)
        if event == "MESSAGE_CREATE":
            print(f"{data['author']['username']}#{data['author']['discriminator']}({data['member']['nick']}): {data['content']}")
finally:
    client.gateway.disconnect()
