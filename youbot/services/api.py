import logging
from flask import Flask, request
app = Flask(__name__)

@app.route("/receive_signup)", methods=["POST"])
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
    return {"status": "ok"}