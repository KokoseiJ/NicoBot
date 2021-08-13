import pytest
from .conftest import wanted_env, unwanted_env

import os
import sys

projpath = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.insert(0, projpath)


@unwanted_env("NO_GATEWAY")
@wanted_env("TOKEN")
class TestClient:
    def test_gets(self, client, guild, channel):
        assert guild == client.get_guild(guild.id)
        assert channel == client.get_channel(channel.id)
        assert client.user == client.get_user(client.user.id)

    def test_update_presence(self, client):
        activity = {
            "name": "Test in progress",
            "type": 0
        }
        client.update_presence(activities=activity, status="dnd")

    @pytest.mark.skip(reason="Known for hanging due to gateway reconnection")
    def test_request_guild_member(self, client, guild):
        client.request_guild_member(guild.id)

    def test_fetches(self, client, guild, channel):
        assert client.user == client.fetch_user(client.user.id)
        assert guild == client.fetch_guild(guild.id)
        assert channel == client.fetch_channel(channel.id)
