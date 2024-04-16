import os
from http import HTTPStatus
from urllib.parse import parse_qs
from twilio.request_validator import RequestValidator
from twilio.rest import Client


def main(args, context):
    body = args.get("http").get("body", {})
    data = parse_qs(body, True)
    data = {k: v[0] for k, v in data.items()}  # convert values to strings
    validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))
    url = os.getenv("TWILIO_WEBHOOK_URL")
    header = args.get("http").get("headers").get("x-twilio-signature", "")
    if not validator.validate(url, data, header):
        return {"statusCode": HTTPStatus.BAD_REQUEST, "body": "invalid signature"}

    return {"statusCode": HTTPStatus.ACCEPTED, "body": body}


def send_message():
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)

    message = client.messages.create(body="Join Earth's mightiest heroes. Like Kevin Bacon.", from_="+15017122661", to="+15558675310")

    print(message.sid)
