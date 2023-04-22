from ._types import Meta, User, handle_error
import requests

from time import time


class Metadata():
    metadata_update_period = 60*60*6  # 6 hours

    def __init__(self, api_key, api_base_url):
        self.api_key = api_key
        self.api_base_url = api_base_url
        # self.is_multiuser = False  # todo implement multiuser for account linking
        # self.users: list = None  # list of users
        self._user = None  # instance of a user
        self._metadata = None
        self._socket_token = None
        self._socket_signature = None
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        self.last_update = None

        # set metadata on initalisation
        self.set_metadata()

    # return metadata as a string
    def __repr__(self):
        return str(self._metadata)

    def set_metadata(self):
        url = self.api_base_url + "metadata/socket"
        response = requests.get(url, headers=self.headers)

        status = response.status_code
        response = response.json()

        if status == 200:
            self._metadata = Meta(response)
            self._user = User(self._metadata.user)
            self.last_update = time()
        else:
            handle_error(status, response, "Meta", "set_metadata")

    def ensure_metadata_updated(self):
        if self._metadata is None or time() - self.last_update > self.metadata_update_period:
            self.set_metadata()

    @property
    def user(self):
        self.ensure_metadata_updated()
        return self._user

    @property
    def socket_token(self):
        self.ensure_metadata_updated()
        return self._metadata.socket_token

    @property
    def socket_signature(self):
        self.ensure_metadata_updated()
        return self._metadata.socket_signature

    @property
    def user_id(self):
        self.ensure_metadata_updated()
        return self._user.id

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
        return self._user.balance

    @property
    def steam_api_key(self):
        self.ensure_metadata_updated()
        return self._user.steam_api_key
