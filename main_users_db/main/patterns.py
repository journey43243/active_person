class Singleton(type):

    _instances = {}

    @classmethod
    def __call__(cls, *args, **kwargs):
        if not cls._instances[cls]:
            super().__call__(*args, **kwargs)
            cls._instances[cls] = cls
        return cls._instances[cls]