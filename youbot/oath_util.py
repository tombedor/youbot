from dataclasses import asdict, dataclass
import json

import requests
import time

from youbot import REDIS_CLIENT
from youbot.data_models import YoubotUser
from google.oauth2.credentials import Credentials

REFRESH_THRESHOLD_SECONDS = 45 * 60


@dataclass
class StoredGoogleCred:
    access_token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list
    epoch_time_seconds: int
    youbot_user_id: int


def get_google_credentials(youbot_user: YoubotUser) -> Credentials:
    stored_credential = _get_stored_credentials(youbot_user)

    if _is_need_refresh(stored_credential):
        access_token = _refresh_access_token(youbot_user)
    else:
        access_token = stored_credential.access_token

    return Credentials(
        token=access_token,
        refresh_token=stored_credential.refresh_token,
        client_id=stored_credential.client_id,
        client_secret=stored_credential.client_secret,
        scopes=stored_credential.scopes,
        token_uri=stored_credential.token_uri,
    )


def persist_google_creds(
    youbot_user: YoubotUser, access_token: str, refresh_token: str, token_uri: str, client_id: str, client_secret: str, scopes: list
):
    stored_cred = StoredGoogleCred(
        access_token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
        epoch_time_seconds=int(time.time()),
        youbot_user_id=youbot_user.id,
    )

    REDIS_CLIENT.setex(_redis_google_creds_key(youbot_user), 3600 * 24, json.dumps(asdict(stored_cred)))  # Store tokens for 24 hours


def _is_need_refresh(stored_google_cred: StoredGoogleCred) -> bool:
    return time.time() - int(stored_google_cred.epoch_time_seconds) > REFRESH_THRESHOLD_SECONDS


def _get_stored_credentials(youbot_user: YoubotUser) -> StoredGoogleCred:
    creds_json = REDIS_CLIENT.get(_redis_google_creds_key(youbot_user))
    if creds_json is None:
        raise KeyError(f"Google credentials for user {youbot_user.id} not found")
    assert type(creds_json) == str

    return StoredGoogleCred(**json.loads(creds_json))


def _redis_google_creds_key(youbot_user: YoubotUser) -> str:
    return f"youbot_google_creds_{youbot_user.id}"


def _refresh_access_token(youbot_user: YoubotUser) -> str:
    creds = _get_stored_credentials(youbot_user)
    assert creds.token_uri is not None

    response = requests.post(
        creds.token_uri,
        data={
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        },
    )
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        persist_google_creds(
            youbot_user=youbot_user,
            access_token=access_token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=creds.scopes,
        )
        return access_token
    else:
        raise ValueError(f"Failed to refresh token: {response.status_code} {response.text}")
