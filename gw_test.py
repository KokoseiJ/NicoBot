from discordapi.client import DiscordClient as Client

import logging

logger = logging.getLogger("NicoBot")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logger.addHandler(ch)

with open("token") as f:
    client = Client(f.read())

client.connect()

try:
    for event, data in client.event_handler.event_generator():
        print(event)
        if event == "MESSAGE_CREATE":
            message = data
            author = message.author
            try:
                nick = message.member.nick
            except AttributeError:
                nick = None
            print(f"{author.username}#{author.discriminator}({nick}): {message.content}")
            if message.content.startswith("?"):
                if author.id == "378898017249525771":
                    if message.content[:6] == "?eval ":
                        try:
                            message.send(eval(message.content[6:]).__repr__())
                        except Exception as e:
                            message.send(f"Error! {e.__class__.__name__}: {e.args[0]}")
                    elif message.content[:6] == "?echo ":
                        message.delete()
                        message.send(message.content[6:])
                else:
                    message.send("だれ?")
finally:
    client.disconnect()
