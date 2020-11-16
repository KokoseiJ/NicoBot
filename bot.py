# NicoBot - Nicovideo player bot for discord, written from the scratch
# Copyright (C) 2020 Wonjun Jung (Kokosei J)
#
#    This program is free software: you can redistribute it and/or modify
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

from discordapi.client import DiscordClient
from discordapi.event import MESSAGE_CREATE
from discordapi.voice import OggParser

import os
import time
import threading
from subprocess import Popen, PIPE, DEVNULL

# get was not used in order to raise exception when TOKEN is not provided, will
# be fixed later
TOKEN = os.environ['TOKEN']

client = DiscordClient(TOKEN)


def vc_test(vc):
    ffmpeg_args = [
        "ffmpeg", "-vn",
        "-i", "nicotest.opus",
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
    pass


try:
    client.gateway.connect()
    print(client.gateway.ready_data)
    for type, event in client.event_generator():
        print(type)
        if type == MESSAGE_CREATE:
            print(event.author, event.content)
            if "?ping" in event.content:
                event.channel.send_message("이쿠사바 무쿠로... 이 학교에 숨은 16번째 고교생... "
                                           "\"초고교급 절망\"이라 불리는 여고생... "
                                           "이쿠사바 무쿠로를 조심해.")
            elif "?connect" in event.content:
                channel_id = event.content.split()[1]
                channel = event.channel.guild.get_channel(channel_id)
                vc = client.voice_connect(channel)
                print("running test")
                threading.Thread(target=vc_test, args=(vc,)).start()
            elif event.content == "?debug":
                cond = client.debug
                client.debug = False if cond else True
                event.channel.send_message(
                    f"Debugging mode is set to {not cond}.")
            elif event.content.startswith("?echo")\
                    and len(event.content.split(" ", 1)) != 1:
                event.channel.send_message(event.content.split(" ", 1)[1])
finally:
    client.gateway.disconnect()
    vc.disconnect()
