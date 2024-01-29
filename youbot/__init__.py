import os
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

for env_var in ['OPENAI_API_KEY', 'GITHUB_TOKEN', 'POSTGRES_URL', 'MEMGPT_CONFIG_PATH']:
    if os.getenv(env_var) is None:
        raise KeyError(f"missing required env var: {env_var}")

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')
MEMGPT_CONFIG_PATH = os.getenv('MEMGPT_CONFIG_PATH')
