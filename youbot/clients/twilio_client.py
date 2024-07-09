import logging
import os
from twilio.rest import Client
from toolz import curry


TWILIO_CHARACTER_LIMIT = 1600

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
sender_number = os.getenv("TWILIO_SENDER_NUMBER")


def prepend_message_length_warning(message: str) -> str:
    return f"[Warning to AI: Reply will be transmitted via Twilio, character length limit is {TWILIO_CHARACTER_LIMIT} characters. Reply in short, concise messages consistent with a text message.]\n{message}"


@curry
def deliver_twilio_message(recipient_phone, message):

    if account_sid and auth_token and sender_number:
        client = Client(account_sid, auth_token)

        if recipient_phone.startswith("whatsapp:"):
            full_sender_number = "whatsapp:" + sender_number
        else:
            full_sender_number = sender_number

        if len(message) > TWILIO_CHARACTER_LIMIT:
            logging.error(f"Message length {len(message)} exceeds character limit {TWILIO_CHARACTER_LIMIT}")
            message = message[:TWILIO_CHARACTER_LIMIT]

        client.messages.create(body=message, to=recipient_phone, from_=full_sender_number)
    else:
        logging.info("TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_SENDER_NUMBER not set. Skipping message delivery.")
