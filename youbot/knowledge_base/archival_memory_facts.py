from typing import List
from youbot.data_models import Fact, YoubotUser
from youbot.store import get_archival_messages


def get_archival_memory_facts(youbot_user: YoubotUser) -> List[Fact]:
    archival_messages = get_archival_messages(youbot_user)
    facts = []
    for archival_message in archival_messages:
        if archival_message.created_at.tzinfo is None:
            # convert to UTC
            time_to_store = archival_message.created_at.replace(tzinfo="UTC")
        else:
            time_to_store = archival_message.created_at

        facts.append(Fact(text=archival_message.text, timestamp=time_to_store))  # type: ignore
    return facts
