import logging
import os
from flask import Flask, request
from youbot import ROOT_DIR
from youbot.store import Store
from youbot.clients.twilio_client import validator, test_recipient, send_message


app = Flask(__name__)


# hacky way to get home page to run
@app.route("/")
def root():
    home_dir = os.path.join(ROOT_DIR, "web", "index.html")
    with open(home_dir, "r") as f:
        return f.read()


@app.route("/api/receive_signup", methods=["POST"])
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
        logging.info(f"received form submission: {name}")

        Store().create_signup(name=name, phone_number=phone_number, discord_member_id=discord_username)

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
    
@app.route("/sms/receive", methods=["POST"])
def sms_reply():
    # TODO: log
    # validate Twilio POST request
    if validator.validate(request.url, request.form, request.headers.get("X-Twilio-Signature", "")):
        logging.info(request.form)
        logging.info(request)
        logging.info(vars(request))
        # process the inbound message, this is just an example
        received_msg = request.form.get("Body")
        logging.info(received_msg)
        send_message(test_recipient, 'thanks for your message!')
        return received_msg, 200

    else:
        return "Validation failed", 403
