import json
import logging
import os
from time import sleep
from typing import List, Optional, Union
from llama_index.embeddings.openai import OpenAIEmbedding

import numpy as np
from openai import OpenAI
import tiktoken

from youbot import cache
from youbot.store import MAX_EMBEDDING_DIM

GPT_SLEEP_SECONDS = 0.4

EMBEDDING_SIZE = 1536
MODEL = "gpt-4o"
TEMPERATURE = 0.0

_embeddings = OpenAIEmbedding(api_base="https://api.openai.com/v1", api_key=os.environ["OPENAI_API_KEY"])


def query_llm(prompt: str, system: Optional[str] = None):
    return _query_llm(prompt=prompt, system=system, model=MODEL, temperature=TEMPERATURE)


@cache.cache()
def _query_llm(prompt: str, system: Optional[str], model: str, temperature: float) -> str:
    logging.debug("llm query: %s...", prompt[0:50])
    if model.startswith("gpt"):
        sleep(GPT_SLEEP_SECONDS)

    if system:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    else:
        msgs = [{"role": "user", "content": prompt}]
    response = OpenAI().chat.completions.create(model=model, messages=msgs, temperature=temperature)  # type: ignore

    first_choice = response.choices[0].message.content
    assert first_choice
    logging.debug("llm response: %s", first_choice)
    return first_choice


def query_llm_json(prompt: str) -> Union[dict, list]:
    return _query_llm_json(prompt=prompt, model=MODEL, temperature=TEMPERATURE)


def count_tokens(s: str) -> int:
    encoding = tiktoken.encoding_for_model(MODEL)
    return len(encoding.encode(s))


@cache.cache()
def _query_llm_json(prompt: str, model: str, temperature: float) -> Union[dict, list]:
    logging.debug("llm query: %s", prompt[0:200])
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


@cache.cache()
def get_embedding(text: str) -> List[float]:
    embedding = _embeddings.get_text_embedding(text)
    embedding = np.array(embedding)
    embedding = np.pad(embedding, (0, MAX_EMBEDDING_DIM - len(embedding)), "constant").to_list()  # type: ignore
    return embedding
