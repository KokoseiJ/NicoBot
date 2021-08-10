import pytest
import os
import sys

projpath = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.insert(0, projpath)

from discordapi import DiscordClient

import time


def wanted_env(envname, reason=None):
    if reason is None:
        reason = f"Env {envname} is not present, skipping..."
    return pytest.mark.skipif(
        not bool(os.environ.get(envname)),
        reason=reason
    )


def unwanted_env(envname, reason=None):
    if reason is None:
        reason = f"Env {envname} is set, skipping..."
    return pytest.mark.skipif(
        bool(os.environ.get(envname)),
        reason=reason
    )


@pytest.fixture(scope="session")
def client():
    token = os.environ.get("TOKEN")
    client = DiscordClient(token=token, intents=32767, name="Test_main")
    client.start()
    client.ready_to_run.wait()
    yield client
    client.stop()


@pytest.fixture(scope="session")
def guild(client):
    guild = None
    while False in client.guilds.values():
        time.sleep(1)

    for obj in client.guilds.values():
        if obj and "TestServer" in obj.name:
            guild = obj
            break

    else:
        pytest.fail("TestServer is not present!", False)

    return guild


@pytest.fixture(scope="session")
def channel(guild):
    channel = None

    for obj in guild.channels.values():
        if obj.name == "test":
            channel = obj
            break

    else:
        pytest.fail("test channel is not present!", False)

    return channel
