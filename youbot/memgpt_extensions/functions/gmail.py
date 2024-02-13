# Send and check email

import os
from simplegmail import Gmail

from youbot import GOOGLE_CREDS_PATH, GOOGLE_EMAIL, SECRETS_DIR
from youbot.service.google_service import fetch_google_email


def send_email(self, subject: str, message: str) -> str:
    """Sends an email to the user's linked google email

    Args:
        subject (str): Subject of the email
        message (str): Body of the email

    Returns:
        str: Description of the result of the email sending attempt.
    """

    email = fetch_google_email(self.agent_state.user_id)
    
    gmail = Gmail(client_secret_file=GOOGLE_CREDS_PATH, creds_file=os.path.join(SECRETS_DIR, 'gmail_creds.json'))

    params = {
        "to": email,
        "sender": GOOGLE_EMAIL,
        "subject": subject,
        # "msg_html": "<h1>Woah, my first email!</h1><br />This is an HTML email.",
        "msg_plain": message,
        "signature": True  # use my account signature
    }
    message = gmail.send_message(**params)
    