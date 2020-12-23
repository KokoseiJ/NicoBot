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
            except:
                continue
            print(f"{author.username}#{author.discriminator}({nick}): {message.content}")
            if author.id == "378898017249525771":
                if message.content[:6] == "?eval ":
                    message.channel.send_message(eval(message.content[6:]))
                elif message.content[:6] == "?echo ":
                    message.channel.send_message(message.content[6:])
finally:
    client.disconnect()
