#
# NicoBot is Nicovideo Player bot for Discord, written from the scratch.
# This file is part of NicoBot.
#
# Copyright (C) 2021 Wonjun Jung (KokoseiJ)
#
#    Nicobot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from discordapi.ogg import OggParser
from discordapi.const import LIB_NAME
from discordapi.client import DiscordClient
from discordapi.handler import GeneratorEventHandler
from discordapi.player import SingleAudioPlayer, FFMPEGAudioSource

import os
import sys
import time
import logging
import threading
from logging import StreamHandler
from websocket._logging import enableTrace
from subprocess import Popen, PIPE, DEVNULL, check_output

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


def vc_test(vc, filename):
    if filename.startswith("yt_http"):
        url = check_output(["youtube-dl", "--get-url", "-f", "bestaudio", filename[3:]])
        filename = url.decode()
    ffmpeg_args = [
        "ffmpeg", "-vn",
        "-i", filename,
        "-f", "opus",
        "-ar", "48000",
        "-ac", "2",
        "-b:a", "96K",
        "-filter:a", "volume=0.5",
        "-"
    ]
    process = Popen(ffmpeg_args, stdin=PIPE, stdout=PIPE, stderr=DEVNULL)
    opus = OggParser(process.stdout)
    vc.speak()
    for packet in opus.packet_iter():
        if not packet:
            continue
        vc._send_voice(packet)
        time.sleep(20/1000)
    vc.speak(0)
    vc.disconnect()
    pass


handler = GeneratorEventHandler()

gw = DiscordClient(
    open("token").read(),
    handler
)

gw.start()
gw.ready_to_run.wait()
logger.info(f"Logged in as {gw.user.username}#{gw.user.discriminator}!")


if __name__ == "__main__":
    try:
        for event, payload in handler.event_generator():
            if event == "MESSAGE_CREATE":
                print(payload.author, payload.content)
                if payload.author.id == gw.user.id:
                    continue
                if "?ping" in payload.content:
                    payload.channel.send("이쿠사바 무쿠로... 이 학교에 숨은 16번째 고교생... "
                                         "\"초고교급 절망\"이라 불리는 여고생... "
                                         "이쿠사바 무쿠로를 조심해.")
                elif payload.content.startswith("?connect"):
                    try:
                        channel_id = payload.content.split()[1]
                        file = payload.content.split()[2]
                        channel = gw.get_channel(channel_id)
                        vc = channel.connect()
                        print("running test")
                        if file.startswith("yt_http"):
                            url = check_output(["youtube-dl", "--get-url", "-f", "bestaudio", file[3:]])
                            filename = url.decode()

                        source = FFMPEGAudioSource(file)
                        player = SingleAudioPlayer(
                            vc, source,
                            lambda:  payload.channel.send("Finished!"))
                        player.play()

                    except:
                        logger.exception("wtf")
                        payload.channel.send("That causes error >:( what have you done")
                elif "?eval" in payload.content and payload.author.id == "378898017249525771":
                    try:
                        payload.channel.send(str(eval(payload.content.split(" ", 1)[-1])))
                    except:
                        logger.exception("wtf")
                        payload.channel.send("that causes error you dumb bitch")
                elif payload.content == "?disconnect":
                    for client in gw.voice_clients:
                        client.disconnect()
                        del client
                    payload.channel.send("Why did you have to do that >:(")
                elif payload.content == "?sleep":
                    if payload.author.id == "378898017249525771":
                        payload.channel.send("okay Good night :wave:")
                        raise KeyboardInterrupt()
                    else:
                        payload.channel.send("No u:heart:")
                elif "?update" in payload.content and payload.author.id == "378898017249525771":
                    is_killed = False
                    process = Popen(["git", "pull"], stdout=PIPE, stderr=PIPE)
                    result = ""
                    try:
                        process.wait()
                    except:
                        is_killed = True
                        process.kill()
                    stdout = process.stdout.read().decode()
                    if is_killed:
                        result += "Timeout occured!\ngit output:```diff\n"
                    elif process.returncode != 0:
                        result += "An error occured!\ngit output:```diff\n"
                    else:
                        result += "Update successful! Restarting...\ngit output:```diff\n"
                    result += stdout
                    result += "```"
                    payload.channel.send(result)
                    if not is_killed and process.returncode == 0:
                        os.system("systemctl restart nicobot")

                elif "?echo" in payload.content:
                    if "pp" in payload.content.split(" "):
                        payload.channel.send("No pp >:(")
                    else:
                        try:
                            payload.channel.send(payload.content.split(" ", 1)[-1])
                        except:
                            logger.exception("rate limit kicks in?")
                            payload.channel.send("I can't send that!")

    except KeyboardInterrupt:
        print("OUCH THAT HURTS")
    finally:
        gw.stop()
        gw.join()

    print("exiting")
