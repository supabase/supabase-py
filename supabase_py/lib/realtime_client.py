from typing import Any, Callable

from realtime_py.connection import Socket
from realtime_py.transformers import convert_change_data


class SupabaseRealtimeClient:
    def __init__(self, socket: Socket, schema: str, table_name: str):
        topic = (
            f"realtime:{schema}"
            if table_name == "*"
            else f"realtime:{schema}:{table_name}"
        )
        self.subscription = socket.set_channel(topic)

    def get_payload_records(self, payload: Any):
        records: dict = {"new": {}, "old": {}}
        columns = payload.get("columns")
        records = payload.get("records")
        old_records = payload.get("old_record")
        if payload.type == "INSERT" or payload.type == "UPDATE":
            records["new"] = payload.record
            convert_change_data(columns, records)
        if payload.type == "UPDATE" or payload.type == "DELETE":
            records["old"] = payload.record
            convert_change_data(columns, old_records)
        return records

    def on(self, event, callback: Callable[..., Any]):
        def cb(payload):
            enriched_payload = {
                "schema": payload.schema,
                "table": payload.table,
                "commit_timestamp": payload.commit_timestamp,
                "event_type": payload.type,
                "new": {},
                "old": {},
            }
            enriched_payload = {**enriched_payload, **self.get_payload_records(payload)}
            callback(enriched_payload)

        self.subscription.join().on(event, cb)
        return self

    def subscribe(self, callback: Callable[..., Any]):
        self.subscription.join().on("ok", callback("SUBSCRIBED")).on(
            "error", lambda x: callback("SUBSCRIPTION_ERROR", x)
        ).on("close", lambda: callback("CLOSED")).on(
            "timeout", lambda: callback("RETRYING_AFTER_TIMEOUT")
        )
        return self.subscription
