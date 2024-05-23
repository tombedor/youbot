from copy import deepcopy
import uuid
from youbot.data_models import YoubotUser
from youbot.clients.memgpt_client import get_agent
from youbot.store import get_youbot_user_by_id
from memgpt.agent import save_agent


def purge_send_message_calls(youbot_user: YoubotUser):
    agent = get_agent(youbot_user)

    agent_messages = []
    new_messages = []
    for m in agent._messages:
        if not m.tool_calls:
            agent_messages.append(m)
        else:
            call = m.tool_calls[0]
            if call.function["name"] == "send_message":
                refactored_message = deepcopy(m)
                refactored_message.text = json.loads(call.function["arguments"])["message"]  # type: ignore
                refactored_message.id = uuid.uuid4()
                refactored_message.tool_calls = None
                new_messages.append(refactored_message)
                agent_messages.append(refactored_message)

    agent.persistence_manager.persist_messages(new_messages)
    agent._messages = agent_messages
    save_agent(agent)


if __name__ == "__main__":
    purge_send_message_calls(get_youbot_user_by_id(1))
