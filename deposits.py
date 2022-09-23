
from calendar import c
from urllib import response
import requests
from ._types import InvalidApiKey, RequestError, ExceedsRatelimit
from ._types import Deposit
from os import environ as env


class Deposits(dict):

    def __init__(self):
        self.api_key = env['api_key']
        self.api_base_url = env['api_base_url']
        self.headers = {'Authorization': f'Bearer {self.api_key}','Content-Type': 'application/json'}
        self.deposit = Deposit()
        
    def get_active_deposits(self):
        url = self.api_base_url+"trading/user/trades"
        response = requests.get(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        active_deposits = []
        app = active_deposits.append
        
        if status == 200:
            for item in response['data']['deposits']:
                app(Deposit(item))
            return active_deposits
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(f"Deposits:get_active_deposits: {response['message']}")
            else:
                raise RequestError(f"Deposits:get_active_deposits: {response['message']}")
            
    def get_inventory(self, force_refresh=False):
        url = self.api_base_url+"trading/user/inventory"+force_refresh
        response = requests.get(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        inventory = []
        app = inventory.append
        
        if status == 200:
            for item in response['data']:
                if "invalid" in item or item['market_value'] < 0 or item['tradable'] == False:
                    continue
                app(Deposit(item))
            return inventory
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(f"Deposits:Get_inv: {response['message']}")
            else:
                raise RequestError(f"Deposits:Get_inv: {response['message']}")