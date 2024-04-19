import logging
import os
from flask import Flask, Response, render_template, request
from youbot import ROOT_DIR
from youbot.clients.memgpt_client import MemGPTClient
from youbot.store import Store
from youbot.clients.twilio_client import test_recipient, send_message, account_sid


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
    phone = data.get("phone")
    discord_username = data.get("discord_username")
    honeypot = data.get("url")

    if honeypot:
        logging.warning("Honeypot triggered")
        return Response(
            {
                "name": name,
                "phone": phone,
                "discord_username": discord_username,
            },
            status=200,
            mimetype="application/json",
        )
    else:
        logging.info(f"received form submission: {name}")
        Store().create_signup(name=name, phone=phone, discord_member_id=discord_username)

        return Response(
            {
                "msg": "Form submitted",
                "name": name,
                "phone": phone,
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
    send_message(message="Hello, World!", receipient_phone=test_recipient)
    return Response("message sent", status=200, mimetype="text/plain")


@app.route("/receive_sms", methods=["POST"])
def sms_receive() -> Response:
    if validate_request(request):
        received_msg = request.form.get("Body")
        assert received_msg
        sender_number = request.form.get("From")
        assert sender_number

        try:
            youbot_user = Store().get_youbot_user_by_phone(phone=sender_number)
            message = f"[the following was sent via SMS, keep responses brief]: {received_msg}"
            response = MemGPTClient.user_message(youbot_user=youbot_user, msg=message)
            send_message(message=response, receipient_phone=sender_number)

        except KeyError:
            logging.warning(f"no user found with phone number {sender_number}")
            return Response({"message": "no user found"}, status=403, mimetype="application/json")

        Store().create_sms_webhook_log(source="receive_sms", msg=str(request.form))
        return Response({"message": received_msg}, status=200, mimetype="application/json")
    else:
        logging.error("failed validation")
        return Response({"message": "invalid signature"}, status=403, mimetype="application/json")


@app.route("/receive_sms_fallback", methods=["POST"])
def sms_fallback() -> Response:
    if validate_request(request):
        logging.info("fallback triggered")
        Store().create_sms_webhook_log(source="sms_fallback", msg=str(request.form))
        return Response({"message": "received"}, status=200, mimetype="application/json")

    else:
        logging.error("rejecting fallback")
        return Response({"message": "invalid signature"}, status=403, mimetype="application/json")


def validate_request(request) -> bool:
    # twilio validation library not working for some reason, instead match SID
    msg_sid = request.form.get("AccountSid")
    if msg_sid != account_sid:
        # TODO: also match phone number against known numbers
        return False
    else:
        return True
