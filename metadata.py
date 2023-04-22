from ._types import Meta, User, handle_error
import requests

from time import time


class Metadata:
    """A class representing user metadata for API authorization and socket connection.

    Attributes:
        api_key (str): The user's API key.
        api_base_url (str): The base URL for API requests.
        headers (dict): The HTTP headers used for API requests.
        last_update (float): The timestamp of the last update to metadata.
        metadata_update_period (int): The duration, in seconds, after which metadata is updated automatically.
        _user (User): An instance of a User object.
        _metadata (Meta): An instance of a Meta object.
        _socket_token (str): A token used for socket authentication.
        _socket_signature (str): A signature used for socket authentication.
    """

    metadata_update_period = 60*60*6  # 6 hours

    def __init__(self, api_key: str, api_base_url: str) -> None:
        """Initializes Metadata object.

        Args:
            api_key (str): The user's API key.
            api_base_url (str): The base URL for API requests.
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self._user = None
        self._metadata = None
        self._socket_token = None
        self._socket_signature = None
        self.headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        self.last_update = None

        # set metadata on initialization
        self.set_metadata()

    def __repr__(self) -> str:
        """Returns metadata as a string."""
        return str(self._metadata)

    def set_metadata(self) -> None:
        """Sets metadata for the user."""
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

    def ensure_metadata_updated(self) -> None:
        """Checks if metadata has been updated and updates if necessary."""
        if self._metadata is None or time() - self.last_update > self.metadata_update_period:
            self.set_metadata()

    @property
    def user(self) -> User:
        """Returns a User object representing the user associated with the API key."""
        self.ensure_metadata_updated()
        return self._user

    @property
    def socket_token(self) -> str:
        """Returns the socket token used for socket authentication."""
        self.ensure_metadata_updated()
        return self._metadata.socket_token

    @property
    def socket_signature(self) -> str:
        """Returns the socket signature used for socket authentication."""
        self.ensure_metadata_updated()
        return self._metadata.socket_signature

    @property
    def user_id(self) -> str:
        """Returns the user ID associated with the API key."""
        self.ensure_metadata_updated()
        return self._user.id

    def get_identify(self) -> dict:
        """Returns a dictionary representing authentication credentials for the socket."""
        self.set_metadata()
        auth = {
            "uid": self.user_id,
            "model": self.user,
            "authorizationToken": self.socket_token,
            "signature": self.socket_signature
        }
        return auth

    @property
    def balance(self) -> float:
        """Returns the user's balance."""
        self.ensure_metadata_updated()
        return self._user.balance
