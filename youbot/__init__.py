import logging
import os
from urllib.parse import urlparse
from redis import StrictRedis
from redis_cache import RedisCache

### NEXT ###
# 1. Update memgpt and no longer rely on config for embedding and llm settings
# 2. Persist embeddings, make available in context manager
# 3. Implement dynamic context system, reminder to do archival memories, etc


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
client = StrictRedis(host=redis_url.hostname, port=redis_url.port, db=0, decode_responses=True)
cache = RedisCache(redis_client=client)
