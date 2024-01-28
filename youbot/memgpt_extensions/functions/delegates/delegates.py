from memgpt import MemGPT
from memgpt.config import MemGPTConfig
from memgpt.data_types import User, AgentState
from memgpt.metadata import MetadataStore
from copy import deepcopy
from uuid import UUID

DEBUGGER = 'debugger'
TESTER = 'tester'


AGENTS = {
    DEBUGGER: {
        'name': 'debuger',
        'preset': 'debugger', 
        'human': 'agent',
        'persona': 'debugger'
    }, 
    TESTER: {
        'name': 'tester',
        'preset': 'tester',
        'human': 'agent',
        'persona': 'tester',
    }
}


# Manages agent instantiation, as well as messaging to agents.
class AgentManager:
    def __init__(self, user_id: UUID, config: MemGPTConfig, llm_config: dict, embedding_config: dict) -> None:
        self.user_id = user_id
        self.ms = MetadataStore(config)
        self.client =  MemGPT(user_id = user_id, auto_save=True, debug=True)
        self.agent_ids = dict(
            (entry['name'], entry['id']) for entry in self.client.list_agents()['agents']
        )

        for agent_name, agent_init_state in AGENTS.iteritems():
            if agent_name not in self.agent_ids:
                new_agent_state = AgentState(
                    **agent_init_state,
                    name=agent_name,
                    user_id=user_id,                    
                    llm_config=llm_config,
                    embedding_config=embedding_config)    
                created_agent_state = self.client.create_agent(vars(new_agent_state))
                self.agent_ids[agent_name] = created_agent_state

    def send_message_to_agent(self, agent_name: str, message:str) -> str:
        response_list = self.client.user_message(self.agent_ids[agent_name], message)
        reply = next(r.get('assistant_message') for r in response_list if r.get('assistant_message'))
        assert reply is not None, "Error during message send, no assistant reply found"
        return reply

_agent_manager_dict = {}
_config = MemGPTConfig.load()

def send_message_to_agent(self, agent_name: str, message: str) -> str:
    """Sends message to an agent. Returns the response from the agent.

    Args:
        agent_name (str): The name of the recipient agent
        message (str): the message to the agent

    Returns:
        str: The response from the recipient agent.
    """
    assert agent_name in AGENTS, f"Agent name must be one of: {AGENTS.keys()}"
    
    user_id = self.agent_state.id
    global _agent_manager_dict
    if user_id not in _agent_manager_dict:
        _agent_manager_dict[user_id] = AgentManager(user_id = user_id, config = _config, llm_config = self.llm_config, embedding_config = self.embedding_config)
    agent_manager = _agent_manager_dict[user_id]        
    return agent_manager.send_message_to_agent(agent_name, message)



    