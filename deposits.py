import requests
from ._types import Deposit, handle_error


class Deposits(dict):
    """
    A class representing a user's deposits. Inherits from a dictionary.

    Attributes:
    - api_key (str): The API key used for authentication.
    - api_base_url (str): The base URL for API requests.
    - headers (dict): The headers to include in API requests.
    - deposit (Deposit): An instance of the Deposit class.
    - can_refresh (bool): Whether or not the server allows for refreshing the inventory.

    Methods:
    - get_active_deposits(): Retrieves a list of the user's active deposits.
    - get_inventory(force_refresh=False): Retrieves the user's inventory.
    """

    def __init__(self, api_key, api_base_url):
        """
        Initializes a new instance of the Deposits class.

        Parameters:
        - api_key (str): The API key used for authentication.
        - api_base_url (str): The base URL for API requests.

        Returns:
        - None
        """

        self.api_key = api_key
        self.api_base_url = api_base_url
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        self.deposit = Deposit(api_key, api_base_url)
        self.can_refresh = False

    def get_active_deposits(self):
        """
        Retrieves a list of the user's active deposits.

        Parameters:
        - None

        Returns:
        - list: A list of the user's active deposits.
        """

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
        """
        Retrieves the user's inventory.

        Parameters:
        - force_refresh (bool): Whether or not to force a refresh of the inventory.

        Returns:
        - list: A list of the user's inventory items.
        """

        # if refresh is requested but server hasn't allowed refresh
        if force_refresh and not self.can_refresh:  
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
                # skip any invalid items or items that are not tradable
                if "invalid" in item or item['market_value'] < 0 or item['tradable'] is False:
                    continue
                app(Deposit(item))
            return inventory
        else:
            handle_error(status, response, "Deposits", "get_inventory")
