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

    def _get_str(self, _class, id, repr=None):
        if repr is not None:
            return f"<{_class} '{repr}' ({id})>"
        else:
            return f"<{_class} ({id})>"

    def __str__(self):
        class_name = self.__class__.__name__
        return self._get_str(class_name, self.id, self.name)
