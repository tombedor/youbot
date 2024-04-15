import logging
from http import HTTPStatus
from urllib.parse import parse_qs
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from flask import Flask, request



app = Flask(__name__)

@app.route("/receive_signup", methods=["POST"])
def receive_signup():
    data = request.get_json()
    name = data.get("name")
    phone_number = data.get("phone_number")
    discord_username = data.get("discord_username")
    honeypot = data.get("url")

    if honeypot:
        logging.warn("Honeypot triggered")
        return {
            "body": {
                "name": name,
                "phone_number": phone_number,
                "discord_username": discord_username,
            },
            "statusCode": 200,
        }
    else:
        return {
            "body": {
                "msg": "Form submitted",
                "name": name,
                "phone_number": phone_number,
                "discord_username": discord_username,
            },
            "statusCode": 200,
        }


@app.route("/health", methods=["GET"])
def health():
    return {
        "body": {
            "message": "healthy",
        },
        "statusCode": 200,
    }

@app.route("/twilio", methods=["POST"])
def sms_reply():
    # replace with your Twilio auth token
    validator = RequestValidator('YOUR AUTH TOKEN')

    # validate Twilio POST request
    if validator.validate(request.url,
                          request.form,
                          request.headers.get('X-Twilio-Signature', '')):

        # process the inbound message, this is just an example
        received_msg = request.form.get('Body')

        # ... code to process the message ...

        # return 200 and received message
        return received_msg, 200

    else:
        return 'Validation failed', 403