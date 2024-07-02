import logging
import os
from urllib.parse import urlparse
from redis import StrictRedis
from redis_cache import RedisCache

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLI_USER_ID = 1

os.environ["MEMGPT_CONFIG_PATH"] = os.path.join(ROOT_DIR, "config", "memgpt_config")


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

redis_url = urlparse(os.environ["REDIS_URL"])
assert redis_url.hostname
assert redis_url.port


if os.environ.get("DEPLOYMENT_ENV", "local") == "production":
    logging.info("Initializing production environment")
    assert redis_url.password
    REDIS_CLIENT = StrictRedis(
        host=redis_url.hostname, port=redis_url.port, db=1, ssl=True, ssl_cert_reqs=None, decode_responses=True, password=redis_url.password  # type: ignore
    )
else:
    logging.debug("Initializing local / development environment")
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))

    REDIS_CLIENT = StrictRedis(host=redis_url.hostname, port=redis_url.port, db=1, ssl=False, decode_responses=True)  # type: ignore
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


assert REDIS_CLIENT.ping()

cache = RedisCache(redis_client=REDIS_CLIENT)
