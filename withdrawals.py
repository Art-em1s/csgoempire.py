import requests
import json
from ._types import handle_error
from time import sleep, time


class Withdrawals(dict):
    """
    A class representing a collection of Withdrawals with methods to interact with the trading API. Inherits from a dictionary.

    Attributes:
        api_key (str): The API key used for authorization.
        api_base_url (str): The base URL for the trading API.
        headers (dict): Headers for making API requests with the API key.

    Methods:
        bid(item_id: int, amount: int) -> bool:
            Place a bid on a listed item.
            Parameters:
                item_id (int): The ID of the item to bid on.
                amount (int): The bid amount.
            Returns:
                True if the bid is successful, otherwise raises an error.

        get_items(per_page: int = 2500, page: int = 1, search: str = "", order: str = "market_value", 
                  sort="desc", auction: str = "yes", price_min: int = 1, price_max: int = 100000,
                  price_max_above: int = 15) -> list:
            Get a list of listed items with the specified filters.
            Parameters:
                per_page (int): Number of items per page.
                page (int): The page number to fetch.
                search (str): A search string to filter items by.
                order (str): The ordering criteria for items.
                sort (str): The sorting order (asc or desc).
                auction (str): Whether or not to include auction items.
                price_min (int): Minimum price for items.
                price_max (int): Maximum price for items.
                price_max_above (int): Maximum price above the market value.
            Returns:
                A list of items matching the specified filters.
    """
    def __init__(self, api_key, api_base_url, *args, **kwargs):
        """
        Initializes a new instance of the Withdrawals class.

        Parameters:
        - api_key (str): The API key used for authentication.
        - api_base_url (str): The base URL for API requests.
        - *args: Variable-length argument list.
        - **kwargs: Arbitrary keyword arguments.

        Returns:
        - None
        """
        super(Withdrawals, self).__init__(*args, **kwargs)
        self.__dict__ = self
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

    def __getattr__(self, attr):
        return self[attr]

    def bid(self, item_id: int, amount: int):
        """
        Place a bid on a listed item.

        Parameters:
        - item_id (int): The ID of the item to bid on.
        - amount (int): The bid amount.

        Returns:
        - True if the bid is successful, otherwise raises an error.
        """
        url = f"{self.api_base_url}trading/deposit/{item_id}/bid"
        data = {"bid_value": amount}
        response = requests.post(url, headers=self.headers, data=json.dumps(data))

        status = response.status_code
        response = response.json()

        if status == 200:
            return True
        else:
            handle_error(status, response, "Withdrawal", "bid")

    def get_items(self, per_page: int = 2500, page: int = 1, search: str = "", order: str = "market_value", sort="desc", auction: str = "yes", price_min: int = 1, price_max: int = 100000, price_max_above: int = 15):
        """
        Get a list of listed items with the specified filters.

        Parameters:
        - per_page (int): Number of items per page.
        - page (int): The page number to fetch.
        - search (str): A search string to filter items by.
        - order (str): The ordering criteria for items.
        - sort (str): The sorting order (asc or desc).
        - auction (str): Whether or not to include auction items.
        - price_min (int): Minimum price for items.
        - price_max (int): Maximum price for items.
        - price_max_above (int): Maximum price above the market value.

        Returns:
        - A list of items matching the specified filters.
        """
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
            handle_error(status, response, "Withdrawal", "get_items")

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
                handle_error(status, response, "Withdrawal", "bid")

            delta = int(time()) - start
            if delta < ratelimit_delay:
                sleep(ratelimit_delay - delta)

        return items
