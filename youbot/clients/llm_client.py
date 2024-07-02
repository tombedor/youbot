import json
import os
from time import sleep
from typing import List, Union
from llama_index.embeddings.openai import OpenAIEmbedding

import numpy as np
from openai import OpenAI
import tiktoken
from toolz import curry, pipe
from toolz.dicttoolz import assoc, merge

from youbot import cache
from youbot.store import MAX_EMBEDDING_DIM

GPT_SLEEP_SECONDS = 0.4

EMBEDDING_SIZE = 1536
MODEL = "gpt-4o"
TEMPERATURE = 0.0

_embeddings = OpenAIEmbedding(api_base="https://api.openai.com/v1", api_key=os.environ["OPENAI_API_KEY"])


@cache.cache()
def _query_llm(prompt: str, system: str, model: str, temperature: float, json_mode: bool) -> str:
    if model.startswith("gpt"):
        sleep(GPT_SLEEP_SECONDS)

    return pipe(
        [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        lambda msgs: {"model": model, "messages": msgs, "temperature": temperature},
        lambda req: assoc(req, "response_format", {"type": "json_object"}) if json_mode else req,
        lambda req: merge(req, {"model": model, "temperature": temperature}),
        lambda req: OpenAI().chat.completions.create(**req),
        lambda response: response.choices[0].message.content,
    )  # type: ignore


@curry
def query_llm(prompt: str, system: str):
    return _query_llm(prompt=prompt, system=system, model=MODEL, temperature=TEMPERATURE, json_mode=False)


@curry
def query_llm_json(prompt: str, system: str) -> Union[dict, list]:
    return json.loads(_query_llm(prompt=prompt, system=system, model=MODEL, temperature=TEMPERATURE, json_mode=True))


def query_llm_with_word_limit(prompt: str, system: str, word_limit: int) -> str:

    return query_llm(
        prompt="\n".join(
            [
                prompt,
                f"Your word limit is {word_limit}. DO NOT EXCEED IT.",
            ]
        ),
        system=system,
    )  # type: ignore


def count_tokens(s: str) -> int:
    encoding = tiktoken.encoding_for_model(MODEL)
    return len(encoding.encode(s))


@cache.cache()
def get_embedding(text: str) -> List[float]:
    embedding = _embeddings.get_text_embedding(text)
    embedding = np.array(embedding)
    embedding = np.pad(embedding, (0, MAX_EMBEDDING_DIM - len(embedding)), "constant").to_list()  # type: ignore
    return embedding
