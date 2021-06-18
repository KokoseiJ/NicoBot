from dictobject import DictObject

GUILD_KEYLIST = ["id", "name", "icon", "icon_hash", "splash",
                 "discovery_splash", "owner", "owner_id", "permissions",
                 "region", "afk_channel_id", "afk_timeout", "widget_enabled",
                 "widget_channel_id", "verification_level",
                 "default_message_notifications", "explicit_content_filter",
                 "roles", "emojis", "features", "mfa_level", "application_id",
                 "system_channel_id", "system_channel_flags",
                 "rules_channel_id", "joined_at", "large", "unavailable",
                 "member_count", "voice_states", "members", "channels",
                 "threads", "presences", "max_presences", "max_members",
                 "vanity_url_code", "description", "banner", "premium_tier",
                 "premium_subscription_count", "preferred_locale",
                 "public_updates_channel_id", "max_video_channel_users",
                 "approximate_member_count", "approximate_presence_count",
                 "welcome_screen", "nsfw_level", "stage_instances"]

KEYLIST = ["id", "type", "guild_id", "position", "permission_overwrites",
           "name", "topic", "nsfw", "last_message_id", "bitrate", "user_limit",
           "rate_limit_per_user", "recipients", "icon", "owner_id",
           "application_id", "parent_id", "last_pin_timestamp", "rtc_region",
           "video_quality_mode", "message_count", "member_count",
           "thread_metadata", "member", "default_auto_archive_duration?"]


class Channel(DictObject):
    def __init__(self, data):
        super(Channel, self).__init__(data, KEYLIST)
