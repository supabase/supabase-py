from realtime_py.connection import Socket


class SupabaseRealtimeClient:
    def __init__(self, socket, schema, table_name):

        topic = (
            f"realtime:{schema}"
            if table_name == "*"
            else f"realtime:{schema}:{table_name}"
        )
        self.subscription = socket.set_channel(topic)

    def get_payload_records(self, payload: Any):
        records = {"new": {}, "old": {}}
        # TODO: Figure out how to create payload
        # if payload.type == "INSERT" or payload.type == "UPDATE":
        #     records.new = Transformers.convertChangeData(payload.columns, payload.record)
        # if (payload.type === 'UPDATE' || payload.type === 'DELETE'):
        #      records.old = Transformers.convertChangeData(payload.columns, payload.old_record)
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
            enriched_payload = {**enriched_payload, **self.getPayloadRecords(payload)}
            callback(enriched_payload)

        self.subscription.join().on(event, cb)
        return self

    def subscribe(self, callback: Callable[..., Any]):
        # TODO: Handle state change callbacks for error and close
        self.subscription.join().on("ok", callback("SUBSCRIBED"))
        self.subscription.join().on(
            "error", lambda x: callback("SUBSCRIPTION_ERROR", x)
        )
        self.subscription.join().on(
            "timeout", lambda: callback("RETRYING_AFTER_TIMEOUT")
        )
        return self.subscription
