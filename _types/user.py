class User(dict):
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __getattr__(self, attr):
        return self[attr]