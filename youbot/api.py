import logging
import os
from typing import Optional
from flask import Flask, Response, render_template, request
from youbot import ROOT_DIR
from youbot.clients.google_client import get_primary_user_info
from youbot.oath_util import persist_google_creds
from youbot.store import create_signup, create_sms_webhook_log, get_youbot_user_by_email, get_youbot_user_by_phone
from youbot.clients.twilio_client import test_recipient, send_message, account_sid
from youbot.workers.worker import response_to_twilio_message

import os
from flask import Flask, redirect, url_for, session, request
from google.auth.exceptions import GoogleAuthError
from google_auth_oauthlib.flow import Flow

GOOGLE_CLIENT_ID = os.environ["YOUBOT_GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["YOUBOT_GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["YOUBOT_GOOGLE_REDIRECT_URI"]
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/contacts.readonly",
    "openid",
]

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


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
    email = data.get("email")
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
        create_signup(name=name, phone=phone, discord_member_id=discord_username, email=email)

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
        flow = _create_flow()
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
        flow = _create_flow(state=state)

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials and extract tokens
        credentials = flow.credentials

        # Fetch user info
        user_info = get_primary_user_info(credentials)
        if user_info:
            email = user_info["email"]
            youbot_user = get_youbot_user_by_email(email)

            assert credentials.token
            assert credentials.refresh_token
            assert credentials.token_uri  # type: ignore
            assert credentials.client_id

            persist_google_creds(
                youbot_user=youbot_user,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,  # type: ignore
                client_id=credentials.client_id,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=GOOGLE_SCOPES,
            )

            # Save the user info and credentials to the session or database
            return redirect(url_for("google_confirmation"))
        else:
            return "Failed to fetch user information from Google."
    except GoogleAuthError as error:
        return f"Authorization error: {error}"
    except Exception as e:
        return f"Unexpected error: {e}"


def _create_flow(state: Optional[str] = None):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=GOOGLE_SCOPES,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
