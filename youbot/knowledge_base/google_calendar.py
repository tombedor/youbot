import os
from cryptography.fernet import Fernet

from youbot.data_models import YoubotUser
from youbot.store import get_encrypted_google_token, store_encrypted_google_token
from google.oauth2.credentials import Credentials
from gcsa.google_calendar import GoogleCalendar


ENCRYPTION_KEY = os.environ["YOUBOT_GOOGLE_ENCRYPTION_KEY"].encode("utf-8")
GOOGLE_CLIENT_ID = os.environ["YOUBOT_GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["YOUBOT_GOOGLE_CLIENT_SECRET"]


def store_token(youbot_user, unencrypted_access_token: str, unencrypted_refresh_token: str):
    f = Fernet(ENCRYPTION_KEY)
    encrypted_access_token = f.encrypt(unencrypted_access_token.encode("utf-8")).decode("utf-8")
    encrypted_refresh_token = f.encrypt(unencrypted_refresh_token.encode("utf-8")).decode("utf-8")
    store_encrypted_google_token(youbot_user, encrypted_access_token, encrypted_refresh_token)


def get_google_calendar_client(youbot_user: YoubotUser) -> GoogleCalendar:
    encrypted_access_token, encrypted_refresh_token = get_encrypted_google_token(youbot_user)
    f = Fernet(ENCRYPTION_KEY)
    access_token = f.decrypt(encrypted_access_token.encode("utf-8")).decode("utf-8")
    refresh_token = f.decrypt(encrypted_refresh_token.encode("utf-8")).decode("utf-8")

    token = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/calendar"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return GoogleCalendar(credentials=token)
