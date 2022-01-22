
from urllib import response
import requests
from ._types import InvalidApiKey, RequestError
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
        elif response['invalid_api_token']:
            raise InvalidApiKey()
        else:
            raise RequestError(response)
            
    def get_inventory(self):
        url = self.api_base_url+"trading/user/inventory"
        response = requests.get(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        inventory = []
        app = inventory.append
        
        if status == 200:
            for item in response['data']:
                app(Deposit(item))
            return inventory
        elif response['invalid_api_token']:
            raise InvalidApiKey()
        else:
            raise RequestError(response)