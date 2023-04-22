from ._types import Meta, InvalidApiKey, User, RequestError, ExceedsRatelimit
import requests

from os import environ as env
from time import time


class Metadata():
    metadata_update_period = 60*60*6  # 6 hours

    def __init__(self):
        # self.is_multiuser = False  # todo implement multiuser for account linking
        # self.users: list = None  # list of users
        self.user: User = None  # instance of user
        self.metadata = None
        self.socket_token = None
        self.socket_signature = None
        self.api_key = env['api_key']
        self.api_base_url = env['api_base_url']
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        self.last_update = None

        # set metadata on initalisation
        self.set_metadata()

    def set_metadata(self):
        url = self.api_base_url + "metadata/socket"
        response = requests.get(url, headers=self.headers)

        status = response.status_code
        response = response.json()

        if status == 200:
            self.metadata = Meta(response)
            self.user = User(self.metadata.user)
            self.last_update = time()
        else:
            self.handle_error(status, response, "set_metadata")

    def ensure_metadata_updated(self):
        if self.metadata is None or time() - self.last_update > self.metadata_update_period:
            self.set_metadata()

    @property
    def user(self):
        self.ensure_metadata_updated()
        return self.metadata.user

    @property
    def socket_token(self):
        self.ensure_metadata_updated()
        return self.metadata.socket_token

    @property
    def socket_signature(self):
        self.ensure_metadata_updated()
        return self.metadata.socket_signature

    @property
    def user_id(self):
        self.ensure_metadata_updated()
        return self.user.id

    def get_identify(self):
        self.set_metadata()  # force get identify to update metadata

        auth = {
            "uid": self.user_id,
            "model": self.user,
            "authorizationToken": self.socket_token,
            "signature": self.socket_signature
        }

        return auth

    @property
    def balance(self):
        self.ensure_metadata_updated()
        return self.user.balance

    @property
    def steam_api_key(self):
        self.ensure_metadata_updated()
        return self.user.steam_api_key

    def handle_error(self, status, response, function_name):
        exception_mapping = {
            401: InvalidApiKey,
            429: ExceedsRatelimit
        }
        exception_class = exception_mapping.get(status, RequestError)
        raise exception_class(f"Meta:{function_name}:{status}: {response['message']}")
