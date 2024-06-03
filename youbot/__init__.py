import logging
import os
from urllib.parse import urlparse
from redis import StrictRedis
from redis_cache import RedisCache

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.environ.get("IS_DEVELOPMENT", False):
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))


CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

redis_url = urlparse(os.environ["REDIS_URL"])
assert redis_url.hostname
assert redis_url.port


if os.environ.get("IS_DEVELOPMENT", False):
    REDIS_CLIENT = StrictRedis(host=redis_url.hostname, port=redis_url.port, db=1, ssl=False, decode_responses=True)  # type: ignore
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

else:
    assert redis_url.password
    REDIS_CLIENT = StrictRedis(
        host=redis_url.hostname, port=redis_url.port, db=1, ssl=True, ssl_cert_reqs=None, decode_responses=True, password=redis_url.password  # type: ignore
    )

assert REDIS_CLIENT.ping()

cache = RedisCache(redis_client=REDIS_CLIENT)

# direct logs to stdout
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
logging.getLogger().handlers.append(logging.StreamHandler())
