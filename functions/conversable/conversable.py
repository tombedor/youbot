from memgpt import MemGPT
from memgpt.config import MemGPTConfig
from memgpt.data_types import User, AgentState
from memgpt.metadata import MetadataStore
from copy import deepcopy

_config = deepcopy(MemGPTConfig.load())
_ms_dict = {}
_client_dict = {}
_user_dict = {}

def _get_vars(self) -> (MetadataStore, MemGPT, User):
    # "user" is the agent.
    user_id = self.agent_state.id
    
    global _ms_dict
    if self.agent_state.id not in _ms_dict:
        ms = MetadataStore(_config)
        _ms_dict[user_id] = ms
    else:
        ms = _ms_dict[user_id]
        
    global _client_dict
    if user_id not in _client_dict:
        client =  MemGPT(user_id = user_id, config = vars(_config), overwrite_config=False)
        _client_dict[user_id] = client
    else:
        client = _client_dict[user_id]

        
    global _user_dict
    if user_id not in _user_dict:
        user = ms.get_user(user_id=user_id)
        if user is None:
            user = ms.create_user(User(id = user_id))
        _user_dict[user_id] = user
    else:
        user = _user_dict[user_id]

    return (ms, client, user)


def send_message_to_agent(self, agent_name: str, message: str) -> str:
    """Sends message to an agent. Returns the response from the agent.

    Args:
        agent_name (str): The name of the recipient agent
        message (str): the message to the agent

    Returns:
        str: The response from the recipient agent.
    """
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
    
    