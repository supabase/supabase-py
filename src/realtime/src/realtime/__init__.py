import logging

# Configure the root logger for the module
logging.getLogger(__name__).addHandler(logging.NullHandler())

from realtime.version import __version__

from ._async.channel import AsyncRealtimeChannel
from ._async.client import AsyncRealtimeClient
from ._async.presence import AsyncRealtimePresence
from ._sync.channel import SyncRealtimeChannel
from ._sync.client import SyncRealtimeClient
from ._sync.presence import SyncRealtimePresence
from .exceptions import *
from .message import *
from .transformers import *
from .types import *
