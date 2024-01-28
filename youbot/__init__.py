import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# load .env

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')
MEMGPT_CONFIG_PATH = os.getenv('MEMGPT_CONFIG_PATH')

for env_var in [
    OPENAI_API_KEY,
    GITHUB_TOKEN,
    POSTGRES_URL,
    MEMGPT_CONFIG_PATH
    ]:
    if env_var is None:
        raise KeyError(f"missing env var: {env_var.__name__}")
    