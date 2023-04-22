

class Item(dict):
    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, attr):
        return self[attr]
