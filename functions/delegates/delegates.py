from memgpt import MemGPT
from memgpt.config import MemGPTConfig
from memgpt.data_types import User, AgentState
from memgpt.metadata import MetadataStore
from copy import deepcopy
from uuid import UUID


AGENTS = {
    'debugger': {
        'name': 'debuger',
        'preset': 'debugger', 
        'human': 'agent',
        'persona': 'debugger'
    }, 
    'tester': {
        'name': 'tester',
        'preset': 'tester',
        'human': 'agent',
        'persona': 'tester',
    }
}

class AgentManager:
    def __init__(self, user_id: UUID, config: MemGPTConfig) -> None:
        self.user_id = user_id
        self.config = config
        self.ms = MetadataStore(config)
        self.client =  MemGPT(user_id = user_id, config = vars(config), overwrite_config=False)
        self.agent_ids = dict(
            (entry['name'], entry['id']) for entry in self.client.list_agents()['agents']
        )

    def get_agent_id(self, agent_name: str, message: str) -> str:
        return self.agent_ids.get(agent_name)

    def is_agent_registered(self, agent_name: str) -> bool:
        return agent_name in self.agent_ids

    def register_agent(self, agent_name: str, id: UUID):
        self.agent_ids[agent_name] = id


_config = deepcopy(MemGPTConfig.load())
_agent_managers = {}


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
    global _agent_managers
    if user_id not in _agent_managers:
        _agent_manager[user_id] = AgentManager(user_id, _config)
    
    agent_manager = _agent_manager[user_id]







    ms, client, user = _get_vars(self)
    
    agent_ids =[d['id'] for d in client.list_agents()['agents'] if d['name'] == agent_name]
    
    
    if len(agent_ids) == 0:
        raise ValueError(f"agent {agent_name} does not exist. Create it first with create_agent! Available agents: {', '.join(agent_names)})")
    else:
        agent_id = agent_ids[0]
        response_list = client.user_message(agent_id, message)
        reply = next(r.get('assistant_message') for r in response_list if r.get('assistant_message'))
        return reply

def create_agent(self, agent_name: str) -> str:
    """Creates an agent if it does not exist

    Args:
        agent_name (str): _description_

    Returns:
        str: Description of the result from the attempt to create an agent.
    """
    ms, client, user = _get_vars(self)
    
    if not client.agent_exists(agent_name):
        
        agent_state = AgentState(
            name=agent_name,
            user_id=user.id,
            persona=self.agent_state.persona,
            human= 'basic',
            preset= self.agent_state.preset,
            llm_config=self.agent_state.llm_config,
            embedding_config=self.agent_state.embedding_config)        
        client.create_agent(vars(agent_state))
        return f"new agent created with name {agent_name}!"
    else:
        return f"agent {agent_name} already exists!"
    
    