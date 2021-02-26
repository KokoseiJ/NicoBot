from discordapi.handler import Handler
from discordapi.client import DiscordClient

import sys
import logging

from logging import StreamHandler

logger = logging.getLogger("NicoBot")
logger.setLevel("DEBUG")

handler = StreamHandler(sys.stdout)
handler.setLevel("DEBUG")

fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|"
                        "%(funcName)s|: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)


class TestHandler(Handler):
    def on_message_create(self, event):
        logger.info(f"{event['author']['username']}#"
                    f"{event['author']['discriminator']}: {event['content']}")
        if event['content'].startswith("!eval"):
            if event['author']['username'] == "KokoseiJ":
                try:
                    data = eval(event['content'].split(" ", 1)[-1])
                    data = str(data)
                except:
                    data = "Error!"
                print(data)
                data = self.client._request(
                    f"channels/{event['channel_id']}/messages",
                    {
                        "content": data,
                        "tts": False,
                        "embed": None,
                        "allowed_mentions": None,
                        "message_reference": {"message_id": event['id'], "guild_id": event['guild_id']}
                        }
                )
                print(data)


gw = DiscordClient(open("token").read(), TestHandler)

try:
    gw.connect()
except KeyboardInterrupt:
    gw.close()
