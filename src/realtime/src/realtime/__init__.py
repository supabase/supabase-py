import logging

# Configure the root logger for the module
logging.getLogger(__name__).addHandler(logging.NullHandler())

from realtime.version import __version__ as __version__

from .channel import RealtimeChannel as RealtimeChannel
from .channel import RealtimeChannelOptions as RealtimeChannelOptions
from .client import RealtimeClient as RealtimeClient
from .client import connect_once as connect_once
from .exceptions import *
from .message import *
from .presence import RealtimePresence as RealtimePresence
from .types import *
