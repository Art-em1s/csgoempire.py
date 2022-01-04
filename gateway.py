import socketio
from signal import SIGINT
from os import kill, getpid, environ
from time import time, sleep
from .metadata import Metadata
from observable import Observable

# TODO:
# Handle reconnection logic
# Cleanup print logging/remove
# docstring connects, see https://discord.com/channels/@me/557952164627087360/926697708222283846 for example
# improve event handling


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
        else:
            print(f"Setup ELSE triggered: {vars(self)}")
    
    def identify(self):
        for i in range(0, 5):
            try:
                self.auth = self.metadata.get_identify()
                self.send('identify', self.auth, namespace='/trade')
                self.is_authed = True
                break
            except:
                print("Failed to identify, retrying...")
                sleep(i)
                continue
        if self.is_authed is False:
            self.events.trigger("on_error", "Failed to identify")
            self.disconnect()
    
    def on(self, event, handler):
        self.events.on(event, handler)
        
    def get_events(self):
        """ Returns the events object
        """
        return self.events
            
    def send(self, event, data, namespace='/trade'):
        self.sio.emit(event, data, namespace)
            
    def disconnect(self):
        self.has_disconnected = True
        self.sio.disconnect()

    def connected(self):
        self.is_connected = True
        if self.is_reconnecting:
            self.events.trigger("on_reconnect", True)
        else:
            self.events.trigger("on_connected", True)
        
    def disconnected(self):
        if self.has_disconnected is False:
            # if the user has not disconnected
            self.is_authed = False
            self.identify()
        else:
            self.is_connected = False
            self.events.trigger("on_disconnected", True)

    
    #todo handle reconnection
        
    def connect_error(self, data):
        self.events.trigger("on_error", data)
        self.disconnect()

    def init_handler(self, data):
        self.is_authed = data['authenticated']
        self.events.trigger("on_init", data)

    def timesync_handler(self):
        # TODO: investigate why this is needed
        now = time() * 1000 # get current time in milliseconds
        self.send('timesync', now)
    
    def new_item_handler(self, data):
        self.events.trigger("on_new_item", data)
        
    def updated_item_handler(self, data):
        self.events.trigger("on_updated_item", data)
        
    def auction_update_handler(self, data):
        self.events.trigger("on_auction_update", data)
        
    def deleted_item_handler(self, data):
        self.events.trigger("on_deleted_item", data)
        
    def trade_status_handler(self, data):
        self.events.trigger("on_trade_status", data)
        
    
        
