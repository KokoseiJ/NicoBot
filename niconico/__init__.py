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

import json
import requests
from base64 import b64decode
from urllib.parse import urljoin
from collections import namedtuple
from threading import Thread, Event
from bs4 import BeautifulSoup as bs

User = namedtuple("User", ("id", "name", "thumbnail"))
Mylist = namedtuple("Mylist", ("id", "name", "description", "owner", "items"))
Video = namedtuple(
    "Video", ("id", "title", "description", "author", "thumbnail", "length")
)


class NicoError(Exception):
    pass


class NicoPlayer:
    LOGIN_URL = "https://account.nicovideo.jp/login/redirector"
    MYLIST_URL = "https://nvapi.nicovideo.jp/v2/mylists/{}?pageSize={}&page={}"
    SEARCH_URL = "https://api.search.nicovideo.jp/" + \
                 "api/v2/snapshot/video/contents/search"
    
    def __init__(self, lang="ja-jp", headers={}, cookies={}, user_agent=None):
        self.lang = lang
        self.logged_in = False
        self.user_id = None
        self.frontend_id = "6"
        self.frontend_version = "0"

        if user_agent:
            self.user_agent = user_agent
        else:
            self.user_agent = "NicoPlayer"

        self.session = requests.session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "x-frontend-id": self.frontend_id,
            "x-frontend-version": self.frontend_version
        })
        self.session.headers.update(headers)
        self.session.cookies.update(cookies)

    def login(self, id, pw):
        self.session.post(
            self.LOGIN_URL,
            data={
                "mail_tel": id,
                "password": pw
            }
        )

        cookie = self.session.cookies.get("user_session_secure")
        if not cookie:
            raise NicoError("Failed to Login.")

        cookie += "=" * (3 - len(cookie) % 3)

        cookie_dec = b64decode(cookie.encode()).decode()
        self.user_id = cookie_dec.split(":", 1)[0]
        self.logged_in = True

    def get_mylist(self, id_):
        pagesize = 100
        index = 1
        items = []
        while True:
            url = self.MYLIST_URL.format(id_, pagesize, index)
            r = self.session.get(url)
            r.raise_for_status()
            data = r.json()["data"]["mylist"]

            _id = data['id']
            name = data['name']
            description = data['description']

            owner_obj = data['owner']
            owner = User(
                owner_obj['id'],
                owner_obj['name'],
                owner_obj['iconUrl']
            )

            items.extend([Video(
                vid['id'],
                vid['title'],
                vid['shortDescription'],
                User(
                    vid['owner']['id'],
                    vid['owner']['name'],
                    vid['owner']['iconUrl']
                ),
                vid['thumbnail']['largeUrl'] if vid['thumbnail']['largeUrl']
                else vid['thumbnail']['nHdUrl'],
                vid['duration']
            ) for vid in [obj['video'] for obj in data['items']]])

            if data['hasNext']:
                index += 1
                continue
            break

        return Mylist(_id, name, description, owner, items)

    def search(self, query, **kwargs):
        arg_dict = {
            "q": query,
            "targets": "title",
            "fields": "contentId,title,description,userId,thumbnailUrl,"
                      "lengthSeconds",
            "_sort": "-viewCounter",
            "_context": self.user_agent
        }
        arg_dict.update(kwargs)
        arg = "&".join([f"{key}={val}" for key, val in arg_dict.items()])
        url = f"{self.SEARCH_URL}?{arg}"

        r = self.session.get(url)
        data = r.json()

        if r.status_code != 200:
            meta = data['meta']
            status = meta['status']
            code = meta['errorCode']
            msg = meta['errorMessage']

            excmsg = f"{status} {code}: {msg}"

            raise NicoError(excmsg)

        result = [Video(
            obj['contentId'],
            obj['title'],
            obj['description'],
            User(obj['userId'], None, None),
            obj['thumbnailUrl'],
            obj['lengthSeconds']
        ) for obj in data['data']]

        return result

    def play(self, id_):
        return NicoDMCVideo(id_, self)


class NicoDMCVideo:
    WATCH_URL = "https://sp.nicovideo.jp/watch/{}"
    GUEST_API_URL = "https://www.nicovideo.jp/api/watch/v3_guest/{}" +\
                    "?actionTrackId={}"
    LOGIN_API_URL = "https://www.nicovideo.jp/api/watch/v3/{}" +\
                    "?actionTrackId={}"

    def __init__(self, id_, client):
        self.client = client
        self.session = client.session
        self.id = id_

        self.heartbeat_thread = None
        self.stop_flag = Event()

        self.watch_data = None
        self.api_data = None
        self.dmc_postdata = None
        self.heartbeat_data = None

        self.action_track_id = None
        self.frontend_id = 6
        self.video_quality = None
        self.audio_quality = None
        self.heartbeat_interval = None
        self.DMC_URL = None
        self.session_id = None
        self.HEARTBEAT_URL = None
        self.m3u8_url = None

        self.title = None
        self.author = None
        self.length = None
        self.thumbnail = None

    def prepare(self, audio=None, video=None):
        self.get_watch_data()
        self.get_api_data()
        
        if audio == "best":
            self.audio_quality = self.audio_quality[:1]
        elif audio == "worst":
            self.audio_quality = self.audio_quality[-1:]

        if video == "best":
            self.video_quality = self.video_quality[:1]
        elif video == "worst":
            self.video_quality = self.video_quality[-1:]

        self.construct_dmc_postdata()
    
    def start(self):
        self.init_dmc()
        self.start_heartbeat()
        return self.m3u8_url

    def get_watch_data(self):
        r = self.session.get(self.WATCH_URL.format(self.id))
        r.raise_for_status()
        soup = bs(r.content, "lxml")
        data_container = soup.find("div", {"id": "jsDataContainer"})
        self.watch_data = json.loads(data_container['data-context'])

        self.action_track_id = self.watch_data['action_track_id']
        self.frontend_id = self.watch_data['frontend_id']
        self.title = self.watch_data['video_title']
        self.author = User(
            self.watch_data['video_author_id'],
            self.watch_data['video_author_name'],
            self.watch_data['video_author_thumbnail_url']
        )
        self.length = self.watch_data['length_in_seconds']
        self.thumbnail = self.watch_data['thumbnail_url']

        return self.watch_data

    def get_api_data(self):
        if self.client.logged_in:
            urlbase = self.LOGIN_API_URL
        else:
            urlbase = self.GUEST_API_URL

        url = urlbase.format(self.id, self.action_track_id)
        headers = {
            "x-frontend-id": str(self.frontend_id),
            "x-frontend-version": "0"
        }

        r = self.session.get(url, headers=headers)
        r.raise_for_status()
        self.api_data = r.json()

        data = self.api_data['data']['media']['delivery']['movie']['session']
        self.video_quality = data['videos']
        self.audio_quality = data['audios']
        self.heartbeat_interval = data['heartbeatLifetime'] / 1000 - 10
        self.DMC_URL = data['urls'][0]['url']

        return self.api_data

    def construct_dmc_postdata(self):
        data = self.api_data['data']['media']['delivery']['movie']['session']
        self.dmc_postdata = {
            "session": {
                "recipe_id": data['recipeId'],
                "content_id": data['contentId'],
                "content_type": "movie",
                "content_src_id_sets": [{
                    "content_src_ids": [{
                        "src_id_to_mux": {
                            "video_src_ids": data['videos'],
                            "audio_src_ids": data['audios']
                        }
                    }]
                }],
                "timing_constraint": "unlimited",
                "keep_method": {
                    "heartbeat": {
                        "lifetime": data['heartbeatLifetime']
                    }
                },
                "protocol": {
                    "name": "http",
                    "parameters": {
                        "http_parameters": {
                            "parameters": {
                                "hls_parameters": {
                                    "use_well_known_port": "yes",
                                    "use_ssl": "yes",
                                    "transfer_preset": "",
                                    "segment_duration": 6000,
                                    "total_duration": self.length * 1000
                                }
                            }
                        }
                    }
                },
                "content_uri": "",
                "session_operation_auth": {
                    "session_operation_auth_by_signature": {
                        "token": data['token'],
                        "signature": data['signature']
                    }
                },
                "client_info": {
                    "player_id": data['playerId']
                },
                "priority": data['priority']
            }
        }

        if self.client.logged_in:
            self.dmc_postdata['session'].update({
                "content_auth": {
                    "auth_type": "ht2",
                    "content_key_timeout": data['contentKeyTimeout'],
                    "service_id": "nicovideo",
                    "service_user_id": self.client.user_id
                }
            })

        return self.dmc_postdata

    def init_dmc(self):
        headers = {"Content-Type": "application/json"}
        data = json.dumps(self.dmc_postdata)
        url = self.DMC_URL + "?_format=json"
        r = self.session.post(url, headers=headers, data=data)
        r.raise_for_status()
        self.heartbeat_data = r.json()['data']
        self.session_id = self.heartbeat_data['session']['id']
        self.HEARTBEAT_URL = urljoin(self.DMC_URL + "/", self.session_id)
        self.m3u8_url = self.heartbeat_data['session']['content_uri']
        return self.m3u8_url

    def start_heartbeat(self):
        self.heartbeat_thread = Thread(
            target=self.do_heartbeat,
            name=f"nico_{self.action_track_id}_heartbeat"
        )
        self.heartbeat_thread.start()

    def do_heartbeat(self):
        url = self.HEARTBEAT_URL + "?_format=json&_method=PUT"
        headers = {"Content-Type": "application/json"}
        while not self.stop_flag.is_set():
            self.stop_flag.wait(self.heartbeat_interval)
            data = json.dumps(self.heartbeat_data)
            r = self.session.post(url, headers=headers, data=data)
            r.raise_for_status()
            self.heartbeat_data = r.json()['data']
