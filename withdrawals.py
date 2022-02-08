import re
import requests, json
from ._types import InvalidApiKey, RequestError, ExceedsRatelimit

from os import environ as env

class Withdrawals(dict):
    def __init__(self, *args, **kwargs):
        super(Withdrawals, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.api_key = env['api_key']
        self.api_base_url = env['api_base_url']
        self.headers = {'Authorization': f'Bearer {self.api_key}','Content-Type': 'application/json'}
    
    def __getattr__(self, attr):
        return self[attr]
    
    def bid(self, item_id: int, amount: int):
        url = self.api_base_url+f"trading/deposit/{item_id}/bid"
        data = {"bid_value":amount}
        response = requests.post(url, headers=self.headers, data=json.loads(data))
        
        status = response.status_code
        response = response.json()
                
        if status == 200:
            return True
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(response['message'])
            else:
                raise RequestError(response)

    def get_items(self, per_page: int = 5000, page: int = 1, search: str = "", order: str = "market_value", sort="desc", auction: str = "yes", price_min: int = 1, price_max: int = 100000, price_max_above: int = 15):
        if search == "":
            url = self.api_base_url+f"trading/items?per_page={per_page}&page={page}&order={order}&sort={sort}&auction={auction}&price_min={price_min}&price_max={price_max}&price_max_above={price_max_above}"
        else:
            url = self.api_base_url+f"trading/items?per_page={per_page}&page={page}&search={search}&order={order}&sort={sort}&auction={auction}&price_min={price_min}&price_max={price_max}&price_max_above={price_max_above}"
        response = requests.get(url, headers=self.headers)
        status = response.status_code
        response = response.json()
        if status == 200:
            return response['data']
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(response['message'])
            else:
                raise RequestError(response)