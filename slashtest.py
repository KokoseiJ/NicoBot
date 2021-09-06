from discordapi.const import LIB_NAME
from discordapi.slash import SlashCommand, String, Integer, DiscordInteractionClient, SubCommandGroup
import sys
import time
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


@SlashCommand.create("meow mhm", (
    String("lmao", "zzlol~"),
    Integer("number_for_test", ".")
))
def testcmd(ctx, lmao, number_for_test):
    return f"1st arg was {lmao}, 2nd arg was {number_for_test}!"


@SlashCommand.create("Updates Command list to Discord", ())
def update(ctx):
    if ctx.user is not None:
        user = ctx.user
    elif ctx.member is not None:
        user = ctx.member.user

    if user.id == "378898017249525771":
        ctx.manager.update()
        return "Sent update request successfully!"
    else:
        return "だれ？"


@SlashCommand.create("cocksex only lol", (
    String("cmd", "fdzz"),
))
def execute(ctx, cmd):
    try:
        return str(eval(cmd))
    except Exception as e:
        name = type(e).__name__
        reason = ", ".join(e.args)
        tbtxt = f"{name}: {reason}"
        return tbtxt


@SlashCommand.create("testing subcommand group", (
    SubCommandGroup("meow", "lolol", (testcmd, update)),
))
def testsubgroup(ctx, meow):
    return meow


@SlashCommand.create("Testing yield/edit", (
    Integer("interval", "Interval to wait", required=True),
))
def testyield(ctx, interval):
    yield f"I will respond again after {interval} seconds..."
    time.sleep(interval)
    yield "... and Here I am!"


print(type(testcmd))
print(json.dumps(testcmd._json(), indent=4))

gw = DiscordInteractionClient(
    open("token").read(),
    intents=32767
)

gw.command_manager.register(testsubgroup)
gw.command_manager.register(update)
gw.command_manager.register(testyield)
gw.command_manager.register(execute)

gw.start()
gw.ready_to_run.wait()
logger.info(f"Logged in as {gw.user.username}#{gw.user.discriminator}!")

if __name__ == "__main__":
    try:
        gw.join()
    except KeyboardInterrupt:
        gw.stop()
