import logging
import os
from flask import Flask, Response, render_template, request
from youbot import ROOT_DIR
from youbot.store import Store
from youbot.clients.twilio_client import validator, test_recipient, send_message


app = Flask(__name__)


# hacky way to get home page to run locally.
@app.route("/")
def root():
    home_dir = os.path.join(ROOT_DIR, "web", "index.html")
    return render_template(home_dir)


@app.route("/receive_signup", methods=["POST"])
def receive_signup() -> Response:
    data = request.get_json()
    name = data.get("name")
    phone_number = data.get("phone_number")
    discord_username = data.get("discord_username")
    honeypot = data.get("url")

    if honeypot:
        logging.warn("Honeypot triggered")
        return Response(
            {
                "name": name,
                "phone_number": phone_number,
                "discord_username": discord_username,
            },
            status=200,
            mimetype="application/json",
        )
    else:
        logging.info(f"received form submission: {name}")

        Store().create_signup(name=name, phone_number=phone_number, discord_member_id=discord_username)

        return Response(
            {
                "msg": "Form submitted",
                "name": name,
                "phone_number": phone_number,
                "discord_username": discord_username,
            },
            status=200,
            mimetype="application/json",
        )


@app.route("/health", methods=["GET"])
def health():
    return Response("healthy", status=200, mimetype="text/plain")


@app.route("/hello_sms", methods=["GET"])
def hello_sms() -> Response:
    send_message("Hello, World!", test_recipient)
    return Response("message sent", status=200, mimetype="text/plain")


@app.route("/receive_sms", methods=["POST"])
def sms_receive() -> Response:
    logging.warn(request.form)
    logging.warn(request)
    logging.warn(vars(request))
    logging.warn(vars(request.headers))
    if validator.validate(request.url, request.form, request.headers.get("X-Twilio-Signature", "")):
        # process the inbound message, this is just an example
        received_msg = request.form.get("Body")
        logging.info(received_msg)
        send_message(test_recipient, "thanks for your message!")
        return Response({"message": received_msg}, status=200, mimetype="application/json")

    else:
        logging.error("failed validation")
        return Response({"message": "invalid signature"}, status=403, mimetype="application/json")
