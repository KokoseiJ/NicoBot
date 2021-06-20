from .user import User
from .const import EMPTY
from .member import Member
from .dictobject import DictObject

__all__ = ["Message"]

KEYLIST = ["id", "channel_id", "guild_id", "author", "member", "content",
           "timestamp", "edited_timestamp", "tts", "mention_everyone",
           "mentions", "mention_roles", "mention_channels", "attachments",
           "embeds", "reactions", "nonce", "pinned", "webhook_id", "type",
           "activity", "application", "application_id", "message_reference",
           "flags", "stickers", "referenced_message", "interaction", "thread",
           "components"]


class Message(DictObject):
    def __init__(self, client, data):
        super(Message, self).__init__(data, KEYLIST)
        self.client = client

        if self.guild_id is not None:
            self.guild = client.guilds.get(self.guild_id)
            if self.guild is not None:
                self.channel = self.guild.channels.get(self.channel_id)

        if self.channel is None:
            self.channel = client.get_channel(self.channel_id)

        self.author = User(client, self.author)
        if self.member is not None:
            self.member = Member(client, self.member)
        self.mentions = [User(client, user) for user in self.mentions]
        if self.referenced_message is not None:
            self.referenced_message = Message(client, self.referenced_message)

    def crosspost(self):
        self.channel.crosspost(self)

    def react(self, emoji, urlencoded=False):
        self.channel.react(self, emoji, urlencoded)

    def delete_my_reaction(self, emoji, urlencoded=False):
        self.channel.delete_my_reaction(self, emoji, urlencoded)

    def delete_others_reaction(self, emoji, user, urlencoded=False):
        self.channel.delete_others_reaction(self, emoji, user, urlencoded)

    def get_reactions(self, emoji, limit=EMPTY, after=EMPTY, urlencoded=False):
        self.channel.get_reactions(self, emoji, limit, after, urlencoded)

    def delete_all_reactions(self):
        self.channel.delete_all_reactions(self)

    def delete_all_reactions_for_emoji(self, emoji, urlencoded=False):
        self.channel.delete_all_reactions_for_emoji(self, emoji, urlencoded)

    def edit(self, content=EMPTY, file=EMPTY, embeds=EMPTY, flags=EMPTY,
             allowed_mentions=EMPTY, attachments=EMPTY, components=EMPTY):
        self.channel.edit_message(self, content, file, embeds, flags,
                                  allowed_mentions, attachments, components)

    def delete(self):
        self.channel.delete_message(self)

    def pin(self):
        self.channel.pin_message(self)

    def unpin(self):
        self.channel.unpin_message(self)

    
