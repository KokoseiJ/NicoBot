from discordapi.const import LIB_NAME
from discordapi.slash import SlashCommand, String, Integer, DiscordInteractionClient
import sys
import json
import logging
from logging import StreamHandler

logger = logging.getLogger(LIB_NAME)
handler = StreamHandler(sys.stdout)
fmt = logging.Formatter("[%(levelname)s]|%(asctime)s|%(threadName)s|"
                        "%(funcName)s|: %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)
if __name__ != "__main__":
    logger.setLevel("DEBUG")
    handler.setLevel("DEBUG")
else:
    logger.setLevel("DEBUG")
    handler.setLevel("DEBUG")


@SlashCommand.create("Command for testing", (
    String("lmao", "zzlol~"),
    Integer("number_for_test", ".")
))
def testcmd(ctx, lmao, number_for_test):
    return


print(type(testcmd))
print(json.dumps(testcmd._json(), indent=4))

gw = DiscordInteractionClient(
    open("token").read(),
    intents=32767
)

gw.command_manager.register(testcmd)

gw.start()
gw.ready_to_run.wait()
logger.info(f"Logged in as {gw.user.username}#{gw.user.discriminator}!")

if __name__ == "__main__":
    try:
        gw.join()
    except KeyboardInterrupt:
        gw.stop()
