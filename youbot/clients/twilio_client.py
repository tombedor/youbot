import os
from twilio.rest import Client

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
sender_number = os.environ["TWILIO_SENDER_NUMBER"]
client = Client(account_sid, auth_token)
test_recipient = os.environ.get("TEST_PHONE_NUMBER")


def hello_world():
    test_recipient = os.environ.get("TEST_PHONE_NUMBER")
    assert test_recipient
    message = client.messages.create(body="Hello, World!", to=test_recipient, from_=sender_number)
    print(message.sid)


def send_message(message, receipient_phone):
    if receipient_phone.startswith("whatsapp:"):
        full_sender_number = 'whatsapp:' + sender_number
    else:
        full_sender_number = sender_number
    
    message = client.messages.create(body=message, to=receipient_phone, from_=full_sender_number)


if __name__ == "__main__":
    hello_world()
