import requests
from .exceptions import RequestError, InvalidApiKey
from .item import Item
from os import environ as env

class Deposit(dict):
    def __init__(self, *args, **kwargs):
        super(Deposit, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.api_key = env['api_key']
        self.api_base_url = env['api_base_url']
        self.headers = {'Authorization': f'Bearer {self.api_key}','Content-Type': 'application/json'}
        
    
    def __getattr__(self, attr):
        return self[attr]
        
    def cancel(self):
        url = self.api_base_url+"trading/deposits/{}/cancel".format(self.id)
        response = requests.post(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        if status == 200:
            return True
        elif response['invalid_api_token']:
            raise InvalidApiKey()
        else:
            raise RequestError(response)
        
    def get_items(self):
        return [Item(item) for item in self.items]
        
    