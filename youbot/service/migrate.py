from youbot.memgpt_client import MemGPTClient
from memgpt.presets.presets import add_default_presets, add_default_humans_and_personas

from memgpt.models.pydantic_models import AgentStateModel, LLMConfigModel, EmbeddingConfigModel, HumanModel, PersonaModel

ms = MemGPTClient.metadata_store


users = ms.get_all_users()

for user in users:
    # add_default_humans_and_personas(user_id=user.id, ms=ms)
    add_default_presets(user_id=user.id, ms=ms)
