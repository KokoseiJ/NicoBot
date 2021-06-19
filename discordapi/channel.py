from .dictobject import DictObject

import json
import base64
from io import IOBase

KEYLIST = ["id", "type", "guild_id", "position", "permission_overwrites",
           "name", "topic", "nsfw", "last_message_id", "bitrate", "user_limit",
           "rate_limit_per_user", "recipients", "icon", "owner_id",
           "application_id", "parent_id", "last_pin_timestamp", "rtc_region",
           "video_quality_mode", "message_count", "member_count",
           "thread_metadata", "member", "default_auto_archive_duration?"]


GUILD_TEXT = 0
DM = 1
GUILD_VOICE = 2
GROUP_DM = 3
GUILD_CATEGORY = 4
GUILD_NEWS = 5
GUILD_STORE = 6
GUILD_NEWS_THREAD = 10
GUILD_PUBLIC_THREAD = 11
GUILD_PRIVATE_THREAD = 12
GUILD_STAGE_VOICE = 13


def get_channel(client, data):
    type = data['type']
    return Channel(client, data)


class Channel(DictObject):
    def __init__(self, client, data):
        super(Channel, self).__init__(data, KEYLIST)

        self.client = client

    def modify_channel(self, name=None, icon=None):
        if isinstance(icon, str):
            with open(icon, "rb") as f:
                icon = base64.b64encode(f.read()).decode()
        elif isinstance(icon, IOBase):
            icon = base64.b64encode(f.read()).decode()
        elif isinstance(icon, bytes):
            icon = base64.b64encode(icon).decode()

        postdata = json.dumps({
            "name": name,
            "icon": icon
        })

        channel_obj = self.client.send_request(
            "PATCH", f"/channels/{self.id}", postdata)
        self.__init__(self.client, channel_obj)
