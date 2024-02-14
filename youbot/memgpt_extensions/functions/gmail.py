# Send and check email

import os
from simplegmail import Gmail

from youbot import GOOGLE_CREDS_PATH, GOOGLE_EMAIL, SECRETS_DIR
from youbot.service.google_service import fetch_google_email


gmail = Gmail(
    client_secret_file=GOOGLE_CREDS_PATH,
    creds_file=os.path.join(SECRETS_DIR, "gmail_creds.json"),
)


def send_email(self, subject: str, message: str) -> str:
    """Sends an email to the user's linked google email

    Args:
        subject (str): Subject of the email
        message (str): Body of the email

    Returns:
        str: Description of the result of the email sending attempt.
    """

    email = fetch_google_email(self.agent_state.user_id)

    params = {
        "to": email,
        "sender": GOOGLE_EMAIL,
        "subject": subject,
        # "msg_html": "<h1>Woah, my first email!</h1><br />This is an HTML email.",
        "msg_plain": message,
        "signature": True,  # use my account signature
    }
    message = gmail.send_message(**params)


# TODO: move to job queue
def respond_to_emails(self):
    """Responds to emails in the user's inbox

    Returns:
        str: Description of the result of the email responding attempt.
    """
    email = fetch_google_email(self.agent_state.user_id)
    messages = gmail.get_unread_inbox(query=f"from:{email} -filename:*ics")
    for message in messages:
        if message.sender != GOOGLE_EMAIL:
            response = f"The following message was received via email. Respond to the email: {message.plain}"
            message.mark_as_read()
            return response
