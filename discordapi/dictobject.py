class DictObject:
    def __init__(self, data, keylist=[]):
        self._json = data
        
        for key in keylist:
            try:
                getattr(self, key)
            except AttributeError:
                setattr(self, key, None)

        for key, value in data.items():
            setattr(self, key, value)
