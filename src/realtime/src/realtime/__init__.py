import logging

# Configure the root logger for the module
logging.getLogger(__name__).addHandler(logging.NullHandler())

from realtime.version import __version__ as __version__

from ._async.channel import AsyncRealtimeChannel as AsyncRealtimeChannel
from ._async.client import AsyncRealtimeClient as AsyncRealtimeClient
from ._async.presence import AsyncRealtimePresence as AsyncRealtimePresence
from ._sync.channel import SyncRealtimeChannel as SyncRealtimeChannel
from ._sync.client import SyncRealtimeClient as SyncRealtimeClient
from ._sync.presence import SyncRealtimePresence as SyncRealtimePresence
from .exceptions import *
from .message import *
from .transformers import *
from .types import *
