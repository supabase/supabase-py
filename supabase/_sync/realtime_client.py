from typing import Any, Dict, List, Optional, Callable
from websockets.sync.client import connect
import json
import threading
import time

class RealtimeMessage:
    def __init__(self, event: str, topic: str, payload: Dict[str, Any], ref: Optional[str] = None):
        self.event = event
        self.topic = topic
        self.payload = payload
        self.ref = ref

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "topic": self.topic,
            "payload": self.payload,
            "ref": self.ref
        }

class RealtimeChannel:
    def __init__(self, topic: str, params: Dict[str, Any] = None):
        self.topic = topic
        self.params = params or {}
        self.subscribed = False
        self.listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._presence_state: Dict[str, Any] = {}

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self.listeners.append(callback)

    def unsubscribe(self) -> None:
        self.listeners = []
        self.subscribed = False

class RealtimeClient:
    def __init__(self, url: str, token: str, **options):
        self.url = url
        self.token = token
        self.options = options
        self.channels: Dict[str, RealtimeChannel] = {}
        self.ws = None
        self._heartbeat_thread = None
        self._connected = False
        self._stop_event = threading.Event()

    def connect(self) -> None:
        self.ws = connect(self.url)
        self._connected = True
        self._stop_event.clear()
        self._start_heartbeat()
        self._start_listener()

    def disconnect(self) -> None:
        self._connected = False
        self._stop_event.set()
        if self.ws:
            self.ws.close()
        if self._heartbeat_thread:
            self._heartbeat_thread.join()

    def channel(self, topic: str, params: Dict[str, Any] = None) -> RealtimeChannel:
        if topic not in self.channels:
            channel = RealtimeChannel(topic, params)
            self.channels[topic] = channel
            if self._connected:
                self._join_channel(channel)
        return self.channels[topic]

    def _join_channel(self, channel: RealtimeChannel) -> None:
        join_message = RealtimeMessage(
            event="phx_join",
            topic=channel.topic,
            payload={"config": channel.params}
        )
        self._send_message(join_message)

    def _start_heartbeat(self) -> None:
        def send_heartbeat():
            while self._connected and not self._stop_event.is_set():
                heartbeat = RealtimeMessage(
                    event="heartbeat",
                    topic="phoenix",
                    payload={}
                )
                self._send_message(heartbeat)
                self._stop_event.wait(30)  # Waits 30s or exits early

        self._heartbeat_thread = threading.Thread(target=send_heartbeat)
        self._heartbeat_thread.daemon = True
        self._heartbeat_thread.start()

    def _start_listener(self) -> None:
        def listen():
            while self._connected:
                try:
                    message = json.loads(self.ws.recv())
                    self._handle_message(message)
                except Exception as e:
                    print(f"Error in listener: {e}")
                    break  # Exit loop on major error

        listener_thread = threading.Thread(target=listen)
        listener_thread.daemon = True
        listener_thread.start()

    def _send_message(self, message: RealtimeMessage) -> None:
        if self.ws and self._connected:
            self.ws.send(json.dumps(message.to_dict()))

    def _handle_message(self, raw_message: Dict[str, Any]) -> None:
        topic = raw_message.get("topic", "")
        if topic in self.channels:
            channel = self.channels[topic]
            for listener in channel.listeners:
                listener(raw_message)
