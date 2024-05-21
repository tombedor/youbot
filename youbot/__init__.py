import logging
import os


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)


if os.environ.get("IS_DEVELOPMENT"):
    # direct logs to stdout
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    logging.getLogger().handlers = [logging.StreamHandler()]
