import requests
from .exceptions import InvalidApiKey, RequestError, ExceedsRatelimit
from os import environ as env
from json import dumps

class Deposit(dict):
    def __init__(self, api_key, api_base_url, *args, **kwargs):
        super(Deposit, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        
    
    def __getattr__(self, attr):
        return self[attr]
        
    def cancel(self):
        url = f"{self.api_base_url}trading/deposits/{self.id}/cancel"
        response = requests.post(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        if status == 200:
            return True
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(f"Deposit:Cancel:{status}: {response['message']}")
            else:
                raise RequestError(f"Deposit:Cancel:{status}: {response['message']}")
        
    def sell_now(self):
        url = f"{self.api_base_url}trading/deposits/{self.id}/sell"
        response = requests.post(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        if status == 200:
            return True
        elif response['invalid_api_token']:
            raise InvalidApiKey()
        else:
            raise RequestError(f"Deposit:SellNow:{status}: {response}")
        
    def list_item(self, percentage):
        url = self.api_base_url+"trading/deposit"
        coin_value = round(self.market_value * (percentage/100+1))
        params = dumps({ "items": [ { "id": self.id, "custom_price_percentage": percentage, "coin_value": coin_value} ] })
        response = requests.post(url, headers=self.headers, data=params)
        
        status = response.status_code
        response = response.json()
        
        if status == 200:
            return True
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(f"Deposit:List_item:{status}: {response['message']}")
            else:
                raise RequestError(f"Deposit:List_item:{status}: {response['message']}")
    