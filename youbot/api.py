import logging
import os
from flask import Flask, Response, render_template, request
from youbot import ROOT_DIR
from youbot.knowledge_base.google_calendar import create_flow, get_user_info, store_tokens
from youbot.store import create_signup, create_sms_webhook_log, get_youbot_user_by_id, get_youbot_user_by_phone
from youbot.clients.twilio_client import test_recipient, send_message, account_sid
from youbot.workers.worker import response_to_twilio_message

import os
from flask import Flask, redirect, url_for, session, request
from google.auth.exceptions import GoogleAuthError


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
        create_signup(name=name, phone=phone, discord_member_id=discord_username)

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
    return {
        "body": {
            "message": "healthy",
        },
        "statusCode": 200,
    }


@app.route("/hello_sms", methods=["GET"])
def hello_sms() -> Response:
    send_message(message="Hello, World!", receipient_phone=test_recipient)
    return Response("message sent", status=200, mimetype="text/plain")


# sms and whatsapp
@app.route("/receive_sms", methods=["POST"])
def sms_receive() -> Response:
    if validate_request(request):
        received_msg = request.form.get("Body")
        assert received_msg
        sender_number = request.form.get("From")
        assert sender_number

        if sender_number.startswith("whatsapp:"):
            user_lookup_number = sender_number.replace("whatsapp:", "")
        else:
            user_lookup_number = sender_number

        try:
            youbot_user = get_youbot_user_by_phone(phone=user_lookup_number)
        except KeyError:
            logging.warning(f"no user found with phone number {user_lookup_number}")
            return Response({"message": "no user found"}, status=403, mimetype="application/json")

        response_to_twilio_message.delay(youbot_user=youbot_user, sender_number=sender_number, received_msg=received_msg)  # type: ignore

        create_sms_webhook_log(source="receive_sms", msg=str(request.form))
        return Response({}, status=200, mimetype="application/json")
    else:
        logging.error("failed validation")
        return Response({"message": "invalid signature"}, status=403, mimetype="application/json")


@app.route("/receive_sms_fallback", methods=["POST"])
def sms_fallback() -> Response:
    if validate_request(request):
        logging.info("fallback triggered")
        create_sms_webhook_log(source="sms_fallback", msg=str(request.form))
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


@app.route("/authorize")
def authorize():
    try:
        # Create flow instance to manage OAuth 2.0 authorization.
        flow = create_flow()
        authorization_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true")

        session["state"] = state

        return redirect(authorization_url)
    except GoogleAuthError as error:
        return f"Authorization error: {error}"
    except Exception as e:
        return f"Unexpected error: {e}"


@app.route("/oauth2callback")
def oauth2callback():
    try:
        state = session["state"]
        flow = create_flow()
        flow.state = state

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials and extract tokens
        credentials = flow.credentials

        # Fetch user info
        user_info = get_user_info(credentials)
        if user_info:
            google_user_id = user_info["sub"]
            email = user_info["email"]

            # Here you should map the Google user to your internal user ID
            # For example: user_id = map_google_user_to_internal_user(google_user_id, email)
            # Mocked internal user ID lookup for demonstration
            user_id = 123  # Replace this with actual mapping logic

            # Save the user info and credentials to the session or database
            session["credentials"] = credentials_to_dict(credentials)  # todo: store instead
            session["user_id"] = user_id
            return redirect(url_for("profile"))
        else:
            return "Failed to fetch user information from Google."
    except GoogleAuthError as error:
        return f"Authorization error: {error}"
    except Exception as e:
        return f"Unexpected error: {e}"
