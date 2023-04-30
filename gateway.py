import socketio
from signal import SIGINT
from os import kill, getpid, environ
from .metadata import Metadata
from observable import Observable
from json import dumps
import threading
from urllib.parse import urlparse


class Gateway:
    # logger
    def __init__(self, api_key, api_base_url, logger=False, engineio_logger=False, domain="csgoempire.com"):
        """
        Constructor method for Gateway class.

        Parameters:
        - api_key (str): User key used to authenticate against the CSGOEmpire API.
        - api_base_url (str): Base URL for the CSGOEmpire API.
        - logger (bool): Whether to enable debug logging or not. Defaults to False.
        - engineio_logger (bool): Whether to enable engineio logging or not. Defaults to False.
        - domain (str): Domain name for the server. Defaults to "csgoempire.com".
        """
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.is_connected = False
        self.is_authed = False
        # triggered when manually disconnected, used to detect if manual dc, denotes reconnect behaviour
        self.has_disconnected = False
        self.is_reconnecting = (
            # triggered prior to reconnection, used to trigger reconnection event
            False
        )
        self.socket = None
        self.auth = None
        self.sio = None
        self.events = None
        self.metadata = Metadata(self.api_key, self.api_base_url)
        self.debug_logger = logger
        self.debug_engineio_logger = engineio_logger
        self.last_status = None
        # remove protocol from domain
        self.domain = urlparse(domain).netloc

    def kill_connection(self):
        """
        Method that force kills the WebSocket connection by sending a SIGINT signal.
        """
        self.is_connected = False
        kill(getpid(), SIGINT)

    def setup(self):
        """
        Method that sets up the WebSocket connection and registers event handlers.
        """
        user_agent = f"{self.metadata.user_id} API Bot | Python Library"
        self.events = Observable()
        if self.is_connected is False and self.socket is None:
            self.sio = socketio.Client(
                logger=self.debug_logger,
                engineio_logger=self.debug_engineio_logger,
                reconnection=True,
            )

            try:
                options = {
                    "url": f"wss://trade.{self.domain}",
                    "socketio_path": "/s/",
                    "headers": {"User-agent": user_agent},
                    "transports": ["websocket"],
                    "namespaces": ["/trade"],
                }
                self.socket = self.sio.connect(**options)
            except Exception as e:
                print(f"WS Connection error: {e} | {options}")

        self.sio.on("connect", handler=self.connected)
        self.sio.on("disconnect", handler=self.disconnected)
        self.sio.on("connect_error", handler=self.connect_error)
        self.sio.on("init", handler=self.init_handler, namespace="/trade")
        self.sio.on("new_item", handler=self.new_item_handler, namespace="/trade")
        self.sio.on(
            "updated_item", handler=self.updated_item_handler, namespace="/trade"
        )
        self.sio.on(
            "auction_update", handler=self.auction_update_handler, namespace="/trade"
        )
        self.sio.on(
            "deleted_item", handler=self.deleted_item_handler, namespace="/trade"
        )
        self.sio.on(
            "trade_status", handler=self.trade_status_handler, namespace="/trade"
        )
        self.sio.on(
            "deposit_failed", handler=self.failed_deposit_handler, namespace="/trade"
        )

    def identify(self):
        """
        Method that sends an "identify" frame to the server to authenticate the user.
        """
        if self.is_authed is False:
            self.auth = self.metadata.get_identify()
            self.send("identify", self.auth, namespace="/trade")

    def emit_filters(self):
        """
        Method that sends a default filter frame to ensure that the client receives all events.
        """
        options = {
            "price_max": 999999,
            "price_max_above": 999,
            "delivery_time_long_max": 9999,
            "auction": "yes",
        }
        self.send("filters", options, namespace="/trade")

    def on(self, event, handler):
        """
        Method that registers an event handler for a specific event.

        Parameters:
        - event (str): Name of the event to register a handler for.
        - handler (function): Handler function to be executed when the event is triggered.
        """
        self.events.on(event, handler)

    def get_events(self):
        """
        Method that returns the events object.

        Returns:
        - events (Observable): Observable object used to register event handlers.
        """
        if self.events is None:
            self.events = Observable()
        return self.events

    def send(self, event, data, namespace="/trade"):
        """
        Method that sends data to the server using the specified event and namespace.

        Parameters:
        - event (str): Name of the event to be sent.
        - data (dict): Data to be sent with the event.
        - namespace (str): Namespace to send the event to. Defaults to "/trade".
        """
        self.sio.emit(event, data, namespace)

    def dc(self):
        """
        Method that disconnects the socket without updating has_disconnected, used in reconnection logic.
        """
        self.is_authed = False  # reset auth
        self.sio.disconnect()

    def disconnect(self):
        """
        Method that disconnects the socket and updates the has_disconnected flag.
        """
        self.has_disconnected = True
        self.sio.disconnect()

    def connected(self):
        """
        Method that is triggered when the WebSocket connection is established or re-established.
        It triggers the on_connected event or the on_reconnect event depending on the situation.
        """
        self.is_connected = True
        self.is_authed = False
        if self.is_reconnecting:
            if self.events is None:
                self.get_events()
            self.events.trigger("on_reconnect", True)
            self.is_reconnecting = False
        else:
            self.events.trigger("on_connected", True)

    def disconnected(self, data=None):
        """
        Method that is triggered when the WebSocket connection is lost.
        It triggers the on_disconnected event with the provided data or True if no data is available.

        Parameters:
        - data (any): Data related to the disconnection event. Defaults to None.
        """
        self.is_connected = False
        self.is_authed = False

        if self.events is not None:
            # Trigger 'on_disconnected' event with either the provided data or True if no data is available
            self.events.trigger("on_disconnected", data if data is not None else True)

        if not self.has_disconnected:
            # If the user has not initiated the disconnection themselves
            self.events = None
            self.is_reconnecting = True

    def connect_error(self, data):
        """
        Method that is triggered when the WebSocket connection encounters an error.
        It maps the connect_error event to the on_error event.

        Args:
            data (dict): Data related to the error
        """
        self.events.trigger("on_error", data)

    def init_handler(self, data):
        """
        Method that maps the init socket event to the on_init event.

        Args:
            data (dict): Data related to the init event
        """
        # sorted_data = dumps(data, indent=4, sort_keys=True)
        self.events.trigger("on_init", data)
        if data["authenticated"]:
            self.is_authed = True
            self.emit_filters()
            self.events.trigger("on_ready", True)
        else:
            self.is_authed = False

    def new_item_handler(self, data):
        """
        Method that maps the new_item socket event to the on_new_item event.

        Parameters:
        - data (dict): Data related to the new item event.
        """
        data = data if isinstance(data, list) else [data]
        for item in data:
            self.events.trigger("on_new_item", item)

    def updated_item_handler(self, data):
        """
        Method that maps the updated_item socket event to the on_updated_item event.

        Parameters:
        - data (dict): Data related to the updated item event.
        """
        data = data if isinstance(data, list) else [data]
        for item in data:
            self.events.trigger("on_updated_item", item)

    def auction_update_handler(self, data):
        """
        Method that maps the auction_update socket event to the on_auction_update event.

        Parameters:
        - data (dict): Data related to the auction update event.
        """
        data = data if isinstance(data, list) else [data]
        for item in data:
            self.events.trigger("on_auction_update", item)

    def deleted_item_handler(self, data):
        """
        Method that maps the deleted_item socket event to the on_deleted_item event.

        Parameters:
        - data (dict): Data related to the deleted item event.
        """
        data = data if isinstance(data, list) else [data]
        for item in data:
            self.events.trigger("on_deleted_item", item)

    def failed_deposit_handler(self, data):
        """
        Method that maps the failed_deposit socket event to the on_failed_deposit event.

        Parameters:
        - data (dict): Data related to the failed deposit event.
        """
        data = data if isinstance(data, list) else [data]
        for item in data:
            self.events.trigger("on_failed_deposit", item)

    def trade_status_handler(self, data):
        """
        Method that handles trade status events and triggers both on_trade_status and the specific event being triggered.

        If `status` is not present in `data`, it uses the last known status of the trade, or skips processing
        if there is no last known status.

        Parameters:
        - data (dict): A dictionary containing information about the trade status event.
        """
        trade_status_enum = {
            -1: "error",
            0: "pending",
            1: "received",
            2: "processing",
            3: "sending",
            4: "confirming",
            5: "sent",
            6: "completed",
            7: "declined",
            8: "canceled",
            9: "timedout",
            10: "credited",
        }
        data = data if isinstance(data, list) else [data]

        # if the trade status is not in the data, use the last status
        for item in data:
            if "status" in item['data'].keys():
                # get the last status
                trade_status = item["data"]["status"]

                # if the last status is not None, use it
                self.last_status = trade_status
            else:
                if self.last_status is not None:
                    trade_status = self.last_status
                else:
                    # if the last status is None, skip processing this event until we have a status to fall back onto
                    return
            self.events.trigger("on_trade_status", item)
            self.events.trigger(f"on_trade_{trade_status_enum[trade_status]}", item)
