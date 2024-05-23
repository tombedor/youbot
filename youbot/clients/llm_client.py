import json
import logging
import os
from time import sleep
from typing import List, Union
from llama_index.embeddings.openai import OpenAIEmbedding

import numpy as np
from openai import OpenAI

from youbot import cache
from youbot.store import MAX_EMBEDDING_DIM

GPT_SLEEP_SECONDS = 0.4

EMBEDDING_SIZE = 1536
MODEL = "gpt-4o"
# MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.0
CACHE_LENGTH_SECONDS = 60 * 60 * 24 * 7

_embeddings = OpenAIEmbedding(api_base="https://api.openai.com/v1", api_key=os.environ["OPENAI_API_KEY"])

MAX_JSON_PARSE_TRIES = 3


def query_llm(prompt):
    return _query_llm(prompt=prompt, model=MODEL, temperature=TEMPERATURE)


@cache.cache(ttl=CACHE_LENGTH_SECONDS)
def _query_llm(prompt: str, model: str, temperature: float) -> str:
    logging.info("llm query: %s...", prompt[0:20])
    if model.startswith("gpt"):
        sleep(GPT_SLEEP_SECONDS)
    response = OpenAI().chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=temperature)

    first_choice = response.choices[0].message.content
    assert first_choice
    logging.debug("llm response: %s", first_choice)
    return first_choice


def query_llm_json(prompt: str) -> Union[dict, list]:
    return _query_llm_json(prompt=prompt, model=MODEL, temperature=TEMPERATURE)


@cache.cache(ttl=CACHE_LENGTH_SECONDS)
def _query_llm_json(prompt: str, model: str, temperature: float) -> Union[dict, list]:
    logging.info("llm query: %s", prompt[0:200])
    if model.startswith("gpt"):
        sleep(GPT_SLEEP_SECONDS)
    response = OpenAI().chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=temperature, response_format={"type": "json_object"}
    )

    first_choice = response.choices[0].message.content
    assert first_choice
    d = json.loads(first_choice)
    logging.debug("llm response: %s", first_choice)
    return d


@cache.cache(ttl=CACHE_LENGTH_SECONDS)
def get_embedding(text: str) -> List[float]:
    embedding = _embeddings.get_text_embedding(text)
    embedding = np.array(embedding)
    embedding = np.pad(embedding, (0, MAX_EMBEDDING_DIM - len(embedding)), "constant").to_list()  # type: ignore
    return embedding
