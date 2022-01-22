import re
import requests, json
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
            return response

    def get_items(self, per_page: int = 5000, page: int = 1, order: str = "desc", auction: str = "yes", price_min: int = 1, price_max: int = 1000, price_max_above: int = 0, search: str = ""):
        if search == "":
            url = self.api_base_url+f"trading/items?per_page={per_page}&page={page}&order={order}&auction={auction}&price_min={price_min}&price_max={price_max}&price_max_above={price_max_above}"
        else:
            url = self.api_base_url+f"trading/items?per_page={per_page}&page={page}&order={order}&auction={auction}&price_min={price_min}&price_max={price_max}&price_max_above={price_max_above}&search={search}"
        return requests.get(url, headers=self.headers).json()        
