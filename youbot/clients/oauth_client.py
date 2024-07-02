from dataclasses import asdict, dataclass
from functools import partial
import json

import requests
import time

from youbot import REDIS_CLIENT
from google.oauth2.credentials import Credentials

from youbot.util import Maybe

from toolz import pipe, curry

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


def get_google_credentials(youbot_user_id: int) -> Maybe[Credentials]:  # type: ignore
    maybe_creds: Maybe[str] = pipe(
        youbot_user_id,
        _redis_google_creds_key,
        lambda key: Maybe(REDIS_CLIENT.get(key)),
    )  # type: ignore

    return (
        maybe_creds.map(json.loads)
        .map(lambda _: StoredGoogleCred(**_))
        .map(
            lambda _: Credentials(
                token=_get_access_token(youbot_user_id, _),
                refresh_token=_.refresh_token,
                client_id=_.client_id,
                client_secret=_.client_secret,
                scopes=_.scopes,
                token_uri=_.token_uri,
            )
        )
    )


def persist_google_creds(
    youbot_user_id: int, access_token: str, refresh_token: str, token_uri: str, client_id: str, client_secret: str, scopes: list
):

    pipe(
        StoredGoogleCred(
            access_token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            epoch_time_seconds=int(time.time()),
            youbot_user_id=youbot_user_id,
        ),
        asdict,
        json.dumps,
        partial(REDIS_CLIENT.setex, _redis_google_creds_key(youbot_user_id), 3600 * 24),
    )


def _redis_google_creds_key(youbot_user_id: int) -> str:
    return f"youbot_google_creds_{youbot_user_id}"


@curry
def _get_access_token(youbot_user_id: int, creds=StoredGoogleCred) -> str:
    if time.time() - int(creds.epoch_time_seconds) > REFRESH_THRESHOLD_SECONDS:
        return creds.access_token

    assert creds is not None
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
            youbot_user_id=youbot_user_id,
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
