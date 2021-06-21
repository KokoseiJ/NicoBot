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

    def __str__(self):
        class_name = self.__class__.__name__
        if self.name is not None:
            return f"<{class_name} {self.name} ({self.id})>"
        else:
            return f"<{class_name} ({self.id})"
