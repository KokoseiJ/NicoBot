from dictobject import DictObject

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


class Channel(DictObject):
    def __init__(self, data):
        super(Channel, self).__init__(data, KEYLIST)
