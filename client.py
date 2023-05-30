from gevent import monkey
monkey.patch_all()

from ._types import *
from .withdrawals import Withdrawals
from .deposits import Deposits
from .gateway import Gateway
from .metadata import Metadata


class Client():
    accepted_domains = [
        "https://csgoempire.com",
        "https://csgoempire.gg",
        "https://csgoempire.tv",
        "https://csgoempiretr.com",
        "https://csgoempire88.com",
        "https://csgoempire.cam",
        "https://csgoempirev2.com",
        "https://csgoempire.io",
        "https://csgoempire.info",
        "https://csgoempire.vip",
        "https://csgoempire.fun",
        "https://csgoempire.biz",
        "https://csgoempire.vegas",
        "https://csgoempire.link"
    ]

    def __init__(self, token=None, domain="https://csgoempire.com", ws_url=None, socket_enabled=True, socket_logger_enabled=False, engineio_logger_enabled=False):
        if token is None:
            raise ApiKeyMissing()
        if len(token) != 32:
            raise InvalidApiKey()

        self.socket_enabled = socket_enabled
        self.socket_logger_enabled = socket_logger_enabled
        self.engineio_logger_enabled = engineio_logger_enabled
        self.ws_url = ws_url

        self.api_key = token
        self.domain = self.normalize_domain(domain)
        self.api_base_url = f"{self.domain}/api/v2/"
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

        # setup metadata
        self.metadata = Metadata(self.api_key, self.api_base_url)
        self.user = self.metadata.user

        # validate api key using set metadata
        self.validate_api_key()

        # if validated, setup deposits/withdrawals
        self.deposits = Deposits(self.api_key, self.api_base_url)
        self.withdrawals = Withdrawals(self.api_key, self.api_base_url)

        # if client initialized with socket enabled, setup gateway
        if socket_enabled:
            # setup socket in background
            self.initalise_socket(logger=socket_logger_enabled, engineio_logger=engineio_logger_enabled)

    @staticmethod
    def normalize_domain(domain):
        if "https://" not in domain.lower():
            domain = f"https://{domain}"
        
        if domain[-1] == "/":
            domain = domain[:-1]
        
        if domain.lower() not in Client.accepted_domains:
            accepted_domains_hr = ',\n'.join(Client.accepted_domains)
            raise InvalidDomain(f"Invalid domain provided\n\nDomain provided:\n{domain}\n\nAccepted domains:\n{accepted_domains_hr}\n\nPlease change your domain to one of these accepted domains.\n")
        return domain

    # metadata related functions

    def get_metadata(self):
        return self.metadata

    def get_balance(self):
        return self.metadata.balance

    def get_socket_token(self):
        return self.metadata.socket_token

    def get_socket_signature(self):
        return self.metadata.socket_signature

    def get_api_token(self):
        return self.api_key

    def get_domain(self):
        return self.domain

    def get_auth_headers(self):
        return self.headers

    def validate_api_key(self):
        if self.metadata.user is None:
            raise InvalidApiKey()

    # user related functions

    def get_user_id(self):
        return self.metadata.user_id

    def get_user(self):
        return self.metadata.user

    def get_steam_api_key(self):
        return self.metadata.user.steam_api_key

    # deposit related functions

    def get_active_deposits(self):
        return self.deposits.get_active_deposits()

    def get_inventory(self, filter: bool = True, force_refresh=False):
        if filter:
            inventory = self.deposits.get_inventory(force_refresh)
            return [item for item in inventory if item['tradable'] is True and item['market_value'] > 0]
        return self.deposits.get_inventory(force_refresh)

    # withdrawal related functions

    def get_auctions(self, **kwargs):
        return self.withdrawals.get_items(**kwargs)

    get_withdrawals = get_auctions

    # gateway related functions

    def disconnect(self):
        self.gateway.disconnect()

    def initalise_socket(self, logger=False, engineio_logger=False):
        # use ws_url if exists, otherwise use domain
        websocket_url = self.ws_url if self.ws_url is not None else self.domain
        # setup gateway
        self.gateway = Gateway(self.api_key, self.api_base_url, logger, engineio_logger, domain=websocket_url, custom_ws_url=self.ws_url is not None)
        self.socket = self.gateway.setup()
        self.events = self.gateway.get_events()

    def kill_connection(self):
        self.gateway.kill_connection()

    def reconnect(self):
        self.gateway.dc()
        self.gateway = None
        self.socket = None
        self.events = None
        self.initalise_socket(logger=self.socket_logger_enabled, engineio_logger=self.engineio_logger_enabled)
