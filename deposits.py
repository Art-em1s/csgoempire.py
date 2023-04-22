import requests
from ._types import Deposit, handle_error

class Deposits(dict):

    def __init__(self, api_key, api_base_url):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        self.deposit = Deposit(api_key, api_base_url)
        self.can_refresh = False

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
            handle_error(status, response, "Deposits", "get_active_deposits")

    def get_inventory(self, force_refresh=False):

        if force_refresh and not self.can_refresh: #if refresh is requested but server hasn't allowed refresh
            force_refresh = False

        url = self.api_base_url+"trading/user/inventory?update="+str(force_refresh)
        response = requests.get(url, headers=self.headers)

        status = response.status_code
        response = response.json()

        inventory = []
        app = inventory.append

        if status == 200:
            self.can_refresh = response['allowUpdate']
            for item in response['data']:
                if "invalid" in item or item['market_value'] < 0 or item['tradable'] is False:
                    continue
                app(Deposit(item))
            return inventory
        else:
            handle_error(status, response, "Deposits", "get_inventory")
