#socketio prevents ctrl+c on windows, gevent fixes this for some reason
# TODO: investigate this and fix (if possible)
from gevent import monkey
monkey.patch_all()

from threading import Thread
from os import environ as env

from .metadata import Metadata
from .gateway import Gateway
from .deposits import Deposits
from .withdrawals import Withdrawals
from ._types import *
from observable import Observable

class Client():
    def __init__(self, token=None, domain="https://csgoempire.com", socket_enabled=True):
        
        if token is None:
            raise ApiKeyMissing()
        elif len(token) != 32:
            raise InvalidApiKey()
        
        self.api_key = token
        
        #todo: compare domain list against list from metadata
        if domain.lower() not in ["https://csgoempire.com", "https://csgoempire.gg"]:
            raise Exception("InvalidDomain", "Domain must be either https://csgoempire.com or https://csgoempire.gg")
        
        self.domain = domain
        self.api_base_url = f"{domain}/api/v2/"
        self.headers = {'Authorization': f'Bearer {self.api_key}','Content-Type': 'application/json'}
        
        #todo: improve this
        env['api_key'] = self.api_key
        env['api_base_url'] = self.api_base_url
        env['domain'] = self.domain
        
        # setup metadata
        self.metadata = Metadata()
        self.user = self.metadata.get_user()
        
        #validate api key using set metadata
        self.validate_api_key()

        #if validated, setup deposits/withdrawals
        self.deposits = Deposits()
        self.withdrawals = Withdrawals()
        
        #if client initalised with socket enabled, setup gateway
        if socket_enabled:
            #setup socket in background
            self.initalise_socket()
            

    #metadata related functions
        
    def get_metadata(self):
        return self.metadata.get_metadata()
        
    def get_socket_token(self):
        return self.metadata.get_socket_token()
    
    def get_socket_signature(self):
        return self.metadata.get_socket_signature()
    
    def get_api_token(self):
        return self.api_key
    
    def get_domain(self):
        return self.domain
    
    def get_auth_headers(self):
        return self.headers
    
    def validate_api_key(self):
        if self.get_metadata()['user'] is None:
            raise InvalidApiKey()
        
    # user related functions
        
    def get_user_id(self):
        return self.metadata.get_user_id()
    
    def get_user(self):
        return self.metadata.get_user()
    
        
    #deposit related functions
    
    def get_active_deposits(self):
        return self.deposits.get_active_deposits()
    
    def get_inventory(self, filter: bool = True):
        if filter:
            inventory = self.deposits.get_inventory()
            return [item for item in inventory if item['tradable'] == True and item['market_value'] > 0]
        else:
            return self.deposits.get_inventory()
        
    #withdrawal related functions
    
    def get_auctions(self, **kwargs):
        return self.withdrawals.get_items(**kwargs)
    
    #gateway related functions
    
    def disconnect(self):
        self.gateway.disconnect()
    
    def initalise_socket(self):
        self.gateway = Gateway()
        self.events = self.gateway.get_events()
        self.socket = Thread(target=self.gateway.setup())