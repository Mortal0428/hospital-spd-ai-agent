import json
import lark_oapi as lark
from lark_oapi.api.im.v1.model.p2_im_message_receive_v1 import P2ImMessageReceiveV1

sample_json = '''{
    "schema": "2.0",
    "header": {
        "event_id": "e123",
        "event_type": "im.message.receive_v1"
    },
    "event": {
        "sender": {
            "sender_id": {"open_id": "ou_8de5ce578af5c5cc4442dc4cd1ff5e42"}
        },
        "message": {
            "message_id": "om_123",
            "chat_id": "oc_4e09defedb59928db5b4b739f9d5e325",
            "chat_type": "group",
            "message_type": "text",
            "content": "{\\"text\\": \\"你是不是个女\\"}"
        }
    }
}'''

event_data = lark.JSON.unmarshal(sample_json, P2ImMessageReceiveV1)
print("Event type:", type(event_data))
event = getattr(event_data, "event", None)
msg = getattr(event, "message", None)
print("chat_id:", getattr(msg, "chat_id", None))
print("chat_type:", getattr(msg, "chat_type", None))
print("mentions:", getattr(msg, "mentions", None))
