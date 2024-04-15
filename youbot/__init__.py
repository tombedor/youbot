import os
from dotenv import load_dotenv
import yaml
import logging
import sys

load_dotenv()

# Expose memgpt config to MemGPT
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(ROOT_DIR, "storage")

os.environ['USER_FUNCTIONS_DIR'] = os.path.join(ROOT_DIR, 'memgpt_extensions', 'functions')

def log_to_stdout():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

os.environ["MEMGPT_CONFIG_PATH"] = os.path.join(ROOT_DIR, "config", "memgpt_config")
with open(os.path.join(ROOT_DIR, "config", "agents.yaml"), "r") as file:
    AGENTS_CONFIG = yaml.safe_load(file.read())

# required env vars
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
