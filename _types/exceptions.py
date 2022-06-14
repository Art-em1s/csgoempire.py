class ApiKeyMissing(Exception):
    def __init__(self):
        self.message = "No token provided, please generate a token at https://csgoempire.com/trading/apikey"

    def __str__(self):
        return self.message
    
class InvalidApiKey(Exception):
    def __init__(self):
        self.message = "Invalid token provided, please generate a token at https://csgoempire.com/trading/apikey"

    def __str__(self):
        return self.message
    
class RequestError(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return self.message
        

#todo: see 'client.py:L21'
class InvalidDomain(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return self.message
    
#todo: see 'client.py:L21'
class ExceedsRatelimit(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return self.message