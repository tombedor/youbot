import os
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMGPT_CONFIG_FILE = os.path.join(os.path.dirname(ROOT_DIR), 'config', 'memgpt_config.yaml')

load_dotenv()

for env_var in ['OPENAI_API_KEY', 'GITHUB_TOKEN', 'POSTGRES_URL']:
    if os.getenv(env_var) is None:
        raise KeyError(f"missing required env var: {env_var}")

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')
os.environ['MEMGPT_CONFIG_PATH'] = MEMGPT_CONFIG_FILE
