import logging
import os
from urllib.parse import urlparse
from redis import StrictRedis
from redis_cache import RedisCache

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

if os.environ.get("IS_DEVELOPMENT"):
    # direct logs to stdout
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    logging.getLogger().handlers = [logging.StreamHandler()]


redis_url = urlparse(os.environ["REDIS_URL"])
assert redis_url.hostname
assert redis_url.port
redis_client = StrictRedis(host=redis_url.hostname, port=redis_url.port, db=0, decode_responses=True)
cache = RedisCache(redis_client=redis_client)

# direct logs to stdout
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
logging.getLogger().handlers.append(logging.StreamHandler())
