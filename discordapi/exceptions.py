class DiscordHTTPError(Exception):
    def __init__(self, code, message, response):
        self.code = code
        self.message = message
        self.response = response

        self.args = (f"{code}: {message}",)
