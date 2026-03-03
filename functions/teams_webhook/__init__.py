"""Azure Function HTTP trigger — receives Teams webhook and queues to Service Bus."""
import json
import logging

try:
    import azure.functions as func
    HAS_AZURE_FUNCTIONS = True
except ImportError:
    HAS_AZURE_FUNCTIONS = False
    func = None


def main(req, context=None):
    """Receive Teams webhook payload and queue for async processing."""
    logging.info("Teams webhook received")
    try:
        if HAS_AZURE_FUNCTIONS:
            body = req.get_json()
        else:
            body = req
    except (ValueError, AttributeError):
        return {"status": 400, "body": "Invalid JSON"}

    user_info = {
        "user_id": body.get("from", {}).get("id", "unknown"),
        "user_email": body.get("from", {}).get("email", "unknown@contoso.com"),
        "user_display_name": body.get("from", {}).get("name", "Unknown User"),
        "message_text": body.get("text", ""),
        "channel_id": body.get("channelId", "general"),
    }

    if not user_info["message_text"]:
        return {"status": 400, "body": "Empty message"}

    try:
        import os
        conn_str = os.environ.get("SERVICE_BUS_CONNECTION_STRING", "")
        if conn_str:
            from azure.servicebus import ServiceBusClient, ServiceBusMessage
            with ServiceBusClient.from_connection_string(conn_str) as sb_client:
                queue_name = os.environ.get("SERVICE_BUS_QUEUE", "it-tickets")
                with sb_client.get_queue_sender(queue_name=queue_name) as sender:
                    sender.send_messages(ServiceBusMessage(json.dumps(user_info)))
        else:
            logging.info(f"LOCAL_MODE: would queue ticket for {user_info['user_email']}")
    except Exception as exc:
        logging.error(f"Queue failed: {exc}")

    result = {"status": "accepted", "message": "Ticket queued for processing"}
    if HAS_AZURE_FUNCTIONS and func:
        return func.HttpResponse(json.dumps(result), status_code=202, mimetype="application/json")
    return result
