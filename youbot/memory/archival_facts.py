from typing import List

from pytz import UTC
from youbot.data_models import Fact
from youbot.store import get_archival_messages

from toolz import pipe
from toolz.curried import map


def get_archival_memory_facts(youbot_user_id: int) -> List[Fact]:
    return pipe(
        youbot_user_id,
        get_archival_messages,
        map(
            lambda _: Fact(
                youbot_user_id=youbot_user_id,
                text=_.text,
                timestamp=_.created_at if _.created_at.tzinfo else _.created_at.replace(tzinfo=UTC),
            ),
        ),
        list,
    )  # type: ignore
