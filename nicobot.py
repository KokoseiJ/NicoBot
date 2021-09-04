from discordapi import DiscordClient, CommandError, CommandManager, CommandEventHandler
from niconico import NicoPlayer
import os
import re

id_ = os.environ.get("ID")
pw = os.environ.get("PW")

player = NicoPlayer()
if id_ and pw:
    player.login(id_, pw)

id_check = re.compile("[a-z]{2}[0-9]+")
watch_check = re.compile(
    "(?:https?\:\/\/)?(?:www.)?nicovideo.jp\/"
    "(?:user\/[0-9]+\/)mylist\/([0-9]+)"
)
mylist_check = re.compile(
    "(?:https?\:\/\/)?(?:www.)?nicovideo.jp\/watch\/([a-z]{2}?[0-9]+)"
)


def check_type(arg):
    match = id_check.match(arg)
    if match:
        return 1, arg
    match = watch_check.match(arg)
    if match:
        return 1, match.groups()[0]
    match = mylist_check.match(arg)
    if match:
        return 2, match.groups()[0]
    else:
        return 0, arg


class NicoBot(CommandManager):
    def play(self, cmd, message):
        type_, val = check_type(cmd)
        if type_ == 0:
            id_ = player.search(val, _limit=1)[0]
        elif type_ == 1:
            id_ = val
