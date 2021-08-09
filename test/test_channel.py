import pytest
from .conftest import wanted_env

import os
import sys

projpath = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.insert(0, projpath)

from discordapi import Channel, Message, File, EMPTY


@wanted_env("TOKEN")
class TestChannel:
    def test_modify(self, channel):
        orig_name = channel.name
        orig_position = channel.position
        orig_topic = channel.topic
        orig_isnsfw = channel.nsfw
        orig_ratelimit = channel.rate_limit_per_user
        orig_permission = channel.permission_overwrites
        orig_parent_id = channel.parent_id

        target_name = "Test in progress"
        target_position = 0
        target_topic = "IA is beautiful"
        target_isnsfw = True
        target_ratelimit = 10
        target_permission = EMPTY
        target_parent_id = None

        mod_chan = channel.modify(
            name=target_name,
            position=target_position,
            topic=target_topic,
            nsfw=target_isnsfw,
            rate_limit_per_user=target_ratelimit,
            permission_overwrites=target_permission,
            parent_id=target_parent_id
        )

        try:
            assert isinstance(mod_chan, Channel)
            assert mod_chan.name == target_name.lower().replace(" ", "-")
            assert mod_chan.position == target_position
            assert mod_chan.topic == target_topic
            assert mod_chan.nsfw == target_isnsfw
            assert mod_chan.rate_limit_per_user == target_ratelimit
            # assert mod_chan.permission_overwrites = target_permission
            assert mod_chan.parent_id == target_parent_id

        finally:
            channel.modify(
                name=orig_name,
                position=orig_position,
                topic=orig_topic,
                nsfw=orig_isnsfw,
                rate_limit_per_user=orig_ratelimit,
                permission_overwrites=orig_permission,
                parent_id=orig_parent_id
            )

    def test_get_messages(self, channel):
        limit = 10
        messages = channel.get_messages(limit=limit)

        assert len(messages) <= limit

        for message in messages:
            assert isinstance(message, Message)

    def test_send(self, channel):
        plain_msg = channel.send(
            content="Testing plain content",
        )

        channel.send(
            content="Testing File",
            file=File(__file__)
        )

        channel.send(
            content="Testing reply_to Message obj behaviour",
            reply_to=plain_msg
        )

        channel.send(
            content="Testing reply_to id behaviour",
            reply_to=plain_msg.id
        )
