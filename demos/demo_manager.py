import os
from urllib.parse import urlparse, urlunparse
from uuid import UUID
from memgpt.metadata import MetadataStore
from memgpt.config import MemGPTConfig
from memgpt.data_types import User


class DemoManager:
    ms = MetadataStore()

    @classmethod
    def run(cls):
        try:
            cls.ms.create_user(User(id=UUID(MemGPTConfig.anon_clientid)))
        except ValueError:
            pass
