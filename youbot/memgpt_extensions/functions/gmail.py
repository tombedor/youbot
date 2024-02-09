# Send and check email

import os
from simplegmail import Gmail

from youbot import GOOGLE_CREDS_PATH, SECRETS_DIR


def send_email(self, message: str) -> str:
    gmail = Gmail(client_secret_file=GOOGLE_CREDS_PATH, creds_file=os.path.join(SECRETS_DIR, 'gmail_creds.json'))

    params = {
    "to": "you@youremail.com",
    "sender": "me@myemail.com",
    "cc": ["bob@bobsemail.com"],
    "bcc": ["marie@gossip.com", "hidden@whereami.com"],
    "subject": "My first email",
    "msg_html": "<h1>Woah, my first email!</h1><br />This is an HTML email.",
    "msg_plain": "Hi\nThis is a plain text email.",
    "attachments": ["path/to/something/cool.pdf", "path/to/image.jpg", "path/to/script.py"],
    "signature": True  # use my account signature
    }
    message = gmail.send_message(**params)