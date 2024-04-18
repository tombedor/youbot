import logging
import os
from twilio.rest import Client
from twilio.request_validator import RequestValidator

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
sender_number = os.environ["TWILIO_SENDER_NUMBER"]
client = Client(account_sid, auth_token)
logging.warn(f"signature: {auth_token}")
validator = RequestValidator(auth_token)
test_recipient = os.environ.get("TEST_PHONE_NUMBER")


def hello_world():
    test_recipient = os.environ.get("TEST_PHONE_NUMBER")
    assert test_recipient
    message = client.messages.create(body="Hello, World!", to=test_recipient, from_=sender_number)
    print(message.sid)


def send_message(message, receipient_phone):
    # TODO: log
    message = client.messages.create(body=message, to=receipient_phone, from_=sender_number)


if __name__ == "__main__":
    hello_world()
