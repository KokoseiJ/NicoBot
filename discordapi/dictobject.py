class DictObject:
    def __init__(self, data, keylist=[]):
        self._json = data
        data.update({key: None for key in keylist})
        for key, value in data.items():
            setattr(self, key, value)
