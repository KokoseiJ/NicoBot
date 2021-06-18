from .gateway import DiscordGateway
from .const import API_URL, LIB_NAME, LIB_VER, LIB_URL

from urllib.request import Request, urlopen


class DiscordClient(DiscordGateway):
    def __init__(self, *args, **kwargs):
        super(DiscordClient, self).__init__(*args, **kwargs)

        self.header = {
            "User-Agent": f"{LIB_NAME} ({LIB_URL}, {LIB_VER})",
            "Authorization": f"Bot {self.token}"
        }
    def _send_request(method, route, expected_code=None, raise_at_exc=False):
        pass
