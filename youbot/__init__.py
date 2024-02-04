import os
from dotenv import load_dotenv
import yaml

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMGPT_CONFIG_FILE = os.path.join(ROOT_DIR, 'config', 'memgpt_config.yaml')
with open(os.path.join(ROOT_DIR, 'config','agents.yaml'), 'r') as file:
    AGENTS_CONFIG = yaml.safe_load(file.read())


for env_var in ['OPENAI_API_KEY', 'GITHUB_TOKEN', 'POSTGRES_URL']:
    if os.getenv(env_var) is None:
        raise KeyError(f"missing required env var: {env_var}")

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
POSTGRES_URL = os.getenv('POSTGRES_URL')

# Expose the config file to memgpt package
os.environ['MEMGPT_CONFIG_PATH'] = MEMGPT_CONFIG_FILE
