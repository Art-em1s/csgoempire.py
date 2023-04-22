import requests, json
from ._types import InvalidApiKey, RequestError, ExceedsRatelimit

from os import environ as env
from time import sleep, time

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
        url = f"{self.api_base_url}trading/deposit/{item_id}/bid"
        data = {"bid_value":amount}
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        
        status = response.status_code
        response = response.json()
                
        if status == 200:
            return True
        else:
            handle_error(status, response)


    def get_items(self, per_page: int = 2500, page: int = 1, search: str = "", order: str = "market_value", sort="desc", auction: str = "yes", price_min: int = 1, price_max: int = 100000, price_max_above: int = 15):
        """Get a list of listed items with the specified filters."""

        items = []
        base_params = {
            "per_page": per_page,
            "order": order,
            "sort": sort,
            "auction": auction,
            "price_min": price_min,
            "price_max": price_max,
            "price_max_above": price_max_above
        }

        if search:
            base_params["search"] = search

        response = requests.get(f"{self.api_base_url}trading/items", headers=self.headers, params={**base_params, "page": page})
        status = response.status_code

        if status == 200:
            response = response.json()
            items.extend(response['data'])
            total_pages = response['last_page']
        else:
            response = response.json()
            self.handle_error(status, response)

        for i in range(page + 1, total_pages + 1):
            ratelimit_delay = 3.1 if search else 3.4

            start = int(time())
            response = requests.get(f"{self.api_base_url}trading/items", headers=self.headers, params={**base_params, "page": i})
            status = response.status_code

            if status == 200:
                response = response.json()
                items.extend(response['data'])
            else:
                response = response.json()
                self.handle_error(status, response)

            delta = int(time()) - start
            if delta < ratelimit_delay:
                sleep(ratelimit_delay - delta)

        return items

            

def handle_error(status, response):
    exception_mapping = {
        401: InvalidApiKey,
        429: ExceedsRatelimit
    }
    exception_class = exception_mapping.get(status, RequestError)
    raise exception_class(f"Withdrawal:Get_items:{status}: {response['message']}")
