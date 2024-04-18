from datetime import UTC, datetime
import uuid

from youbot.store import YoubotUser


import pytest
from pydantic import ValidationError
from youbot.store import YoubotUser  # make sure to import your model correctly


@pytest.fixture
def user():
    yield YoubotUser(
        id=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        name="foo",
        memgpt_user_id=uuid.uuid4(),
        memgpt_agent_id=uuid.uuid4(),
        discord_member_id="1234567890",
        phone="+12345678901",
        human_description="nice man",
    )


def test_phone_happy(user: YoubotUser):
    # Test a valid E.164 number
    good_phone = "+12345678901"
    user.phone = good_phone
    YoubotUser.model_validate(user)


def test_phone_sad(user: YoubotUser):
    bad_phone = "12345678901"
    user.phone = bad_phone
    with pytest.raises(ValidationError):
        user = YoubotUser(phone=bad_phone)  # type: ignore
        YoubotUser.model_validate(user)
