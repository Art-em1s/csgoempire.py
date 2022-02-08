from ._types import Meta, InvalidApiKey, User, RequestError, ExceedsRatelimit
import requests

from os import environ as env


class Metadata():
    def __init__(self):
        self.is_multiuser = False #todo implement multiuser for account linking
        self.user: User = None #instance of user
        self.users: list = None #list of users
        self.metadata = None
        self.socket_token = None
        self.socket_signature = None
        self.api_key = env['api_key']
        self.api_base_url = env['api_base_url']
        self.headers = {'Authorization': f'Bearer {self.api_key}','Content-Type': 'application/json'}
        
        
        #set metadata on initalisation
        self.get_metadata()
        
    def set_metadata(self):
        url = self.api_base_url + "metadata/socket"
        response = requests.get(url, headers=self.headers)
        
        status = response.status_code
        response = response.json()
        
        if status == 200:
            self.metadata = Meta(response)
            self.user = User(self.metadata.user)
        else:
            if status == 401:
                raise InvalidApiKey()
            elif status == 429:
                raise ExceedsRatelimit(response['message'])
            else:
                raise RequestError(response)
        
    def get_metadata(self):
        if self.metadata is None:
            self.set_metadata()
        return self.metadata    
        
    def get_user(self):
        if self.metadata is None:
            self.set_metadata()
            
        return self.metadata.user
                
    def get_socket_token(self):
        if self.metadata is None:
            self.set_metadata()
        return self.metadata.socket_token
        
    def get_socket_signature(self):
        if self.metadata is None:
            self.set_metadata()
        return self.metadata.socket_signature
    
    def get_user_id(self):
        if self.metadata is None:
            self.set_metadata()
            
        return self.user.id
        
    def get_identify(self):
        self.set_metadata() #force get idenitfy to update metadata
            
        auth = {
            "uid": self.get_user_id(),
            "model": self.get_user(),
            "authorizationToken": self.get_socket_token(),
            "signature": self.get_socket_signature()
        }
        
        return auth