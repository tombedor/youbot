import base64
from hashlib import sha1
import hmac
import logging
import os
import re
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
    logging.warn("REQUEST URL = " + request.url)
    logging.warn("REQUEST FORM = " + str(request.form))
    logging.warn("REQUEST HEADERS = " + str(request.headers))
    signature = request.headers.get("X-Twilio-Signature", "")
    logging.warn(f"TWILIO_SIG = {signature}")
    manual_validate(request)
    
    valid_with_body = validator.validate(request.url, request.form, signature)
    logging.warn(f"VALID_WITH_BODY = {valid_with_body}")
    valid_without_body = validator.validate(request.url, {}, signature)
    logging.warn(f"VALID_WITHOUT_BODY = {valid_without_body}")
    if validator.validate(request.url, request.form, request.headers.get("X-Twilio-Signature", "")):
        # process the inbound message, this is just an example
        received_msg = request.form.get("Body")
        logging.info(received_msg)
        send_message(test_recipient, "thanks for your message!")
        return Response({"message": received_msg}, status=200, mimetype="application/json")

    else:
        logging.error("failed validation")
        return Response({"message": "invalid signature"}, status=403, mimetype="application/json")



def manual_validate(request):
    try:
        twil_sig = request.headers['X-Twilio-Signature']
        logging.warn(f"X-Twilio-Signature: {twil_sig}")
    except KeyError:
        return('No X-Twilio-Signature. This request likely did not originate from Twilio.', 418) 
    # domain = re.sub('http', 'https', request.url)
    domain = request.url
    if request.form:
        for k, v in sorted(request.form.items()):
            domain += k + v
    else:
      return ('Bad Request - no form params', 400) 
  
    mac = hmac.new(bytes(os.environ['TWILIO_AUTH_TOKEN'], 'UTF-8'), domain.encode("utf-8"), sha1)
    computed = base64.b64encode(mac.digest())   
    computed = computed.decode('utf-8')
    diy_signature = computed.strip()
    logging.warn(f"DIY_SIG = {diy_signature}")
    
    if diy_signature != twil_sig:
        logging.warn("No match!")
        return False
    else:
        logging.warn("match!")
        return True
        

