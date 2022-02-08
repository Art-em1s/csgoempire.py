import socketio
from signal import SIGINT
from os import kill, getpid, environ
from time import time, sleep
from .metadata import Metadata
from observable import Observable

# TODO:
# docstring comments, see https://discord.com/channels/@me/557952164627087360/926697708222283846 for example


class Gateway:
    def __init__(self):
        self.is_connected = False # is the socket connected
        self.is_authed = False # is the user authenticated
        self.has_disconnected = False #triggered when manually disconnected, used to detect if manual dc, denotes reconnect behaviour
        self.is_reconnecting = False #triggered prior to reconnection, used to trigger reconnection event
        self.socket = None
        self.auth = None
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.events = Observable()
        self.metadata = Metadata()
        
    def kill_connection(self):
        """ Kill the WS connection via SIGINT
        """        
        self.is_connected = False
        kill(getpid(), SIGINT)
        
    def setup(self):
        if self.is_connected is False and self.socket is None:
            user_agent = f"{self.metadata.get_user_id()} API Bot | Python Library"
            self.sio.on("connect", handler=self.connected)
            self.sio.on("disconnect", handler=self.disconnected)
            self.sio.on("connect_error", handler=self.connect_error)
            
            self.sio.on("init", handler=self.init_handler, namespace='/trade')
            self.sio.on("new_item", handler=self.new_item_handler, namespace='/trade')
            self.sio.on("updated_item", handler=self.updated_item_handler, namespace='/trade')
            self.sio.on("auction_update", handler=self.auction_update_handler, namespace='/trade')
            self.sio.on("deleted_item", handler=self.deleted_item_handler, namespace='/trade')
            self.sio.on("trade_status", handler=self.trade_status_handler, namespace='/trade')
            #allow for .gg or .com 
            domain = environ['domain'].split('/')[-1]
            self.socket = self.sio.connect(url=f'wss://trade.{domain}', socketio_path='/s/', headers={"User-agent": user_agent}, transports=['websocket'], namespaces=['/trade'])
    
    def identify(self):
        """ Fires the identify frames to the server, identifying the user
        """        
        # Retry sending identify if it fails up to 5 times, with an increased delay between frames
        for i in range(0, 5):
            sleep(i)
            if self.is_authed is False:
                self.auth = self.metadata.get_identify()
                self.send('identify', self.auth, namespace='/trade')
            else:
                break
            if i>0:
                self.events.trigger("on_error", {"error": f"Failed to identify. Retry attempt {i}"})
        if self.is_authed is False:
            self.events.trigger("on_error", {"error": "Failed to identify. Retry attempts exhausted"})
            self.disconnect()
        else:
            self.events.trigger("on_ready", True)
    
    def on(self, event, handler):
        self.events.on(event, handler)
        
    def get_events(self):
        """ Returns the events object
        """
        return self.events
            
    def send(self, event, data, namespace='/trade'):
        self.sio.emit(event, data, namespace)
            
    def disconnect(self):
        """ Disconnects the socket
        """        
        self.has_disconnected = True
        self.sio.disconnect()

    def connected(self):
        """ Trigger the on_connected event on first connection and on_reconnection if connection is re-established
        """        
        self.is_connected = True
        if self.is_reconnecting:
            self.events.trigger("on_reconnect", True)
        else:
            self.events.trigger("on_connected", True)
        
    def disconnected(self):
        """ Built in function for handling disconnection triggers reconnection if not manually disconnected
        """        
        if self.has_disconnected is False:
            # if the user has not disconnected
            self.is_authed = False
            self.identify()
        else:
            self.is_connected = False
            self.events.trigger("on_disconnected", True)

    def connect_error(self, data):
        """Map the connect_error event to the on_error event

        Args:
            data (dict): Data related to the error
        """        
        self.events.trigger("on_error", data)
        self.disconnect()

    def init_handler(self, data):
        """Map the init socket event to the on_init event

        Args:
            data (dict): Data related to the init event
        """        
        self.is_authed = data['authenticated']
        self.events.trigger("on_init", data)

    def timesync_handler(self):
        # TODO: investigate why this is needed
        now = time() * 1000 # get current time in milliseconds
        self.send('timesync', now)
    
    def new_item_handler(self, data):
        """Map the new item socket event to the on_new_item event

        Args:
            data (dict): Data related to the new item event
        """   
        self.events.trigger("on_new_item", data)
        
    def updated_item_handler(self, data):
        """Map the updated item socket event to the on_updated_item event

        Args:
            data (dict): Data related to the updated item event
        """        
        self.events.trigger("on_updated_item", data)
        
    def auction_update_handler(self, data):
        """Map the auction update socket event to the on_auction_update event

        Args:
            data (dict): Data related to the auction update event
        """        
        self.events.trigger("on_auction_update", data)
        
    def deleted_item_handler(self, data):
        """Map the deleted item socket event to the on_deleted_item event

        Args:
            data (dict): Data related to the deleted item event
        """        
        self.events.trigger("on_deleted_item", data)
        
    def trade_status_handler(self, data):
        """ Handles trade status, this triggers both on_trade_status & the specific event being triggered here
        
        For example:
        
        A trade with the status of -1 would trigger both on_trade_status & on_trade_error

        Args:
            data (dict): Data related to the trade_status event
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
        10: "credited"
        }
        #trigger on_trade_status event
        self.events.trigger("on_trade_status", data)
        
        #trigger specific event based on trade status
        trade_status = data['data']['status']
        self.events.trigger(f"on_trade_{trade_status_enum[trade_status]}", data)
    
        
