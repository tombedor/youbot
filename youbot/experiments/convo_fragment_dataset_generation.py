from hashlib import md5
import subprocess

from openai import OpenAI
from tqdm import tqdm

from youbot.json_decoder import parse_json
from datasets import Dataset

import os
from openai import OpenAI


def get_response(fact):
  client = OpenAI(
      # This is the default and can be omitted
      api_key=os.environ.get("OPENAI_API_KEY"),
  )
  prompt = f"""
As an understanding language model, your mission is to
construct twenty five unique conversational fragments
representing the same fact - '{fact}'

Remember, each fragment should provide a fresh
perspective while efficiently conveying '{fact}' 
"""
  chat_completion = client.chat.completions.create(
      messages=[
          {
              "role": "user",
              "content": prompt,
          }
          
      ],
      model="gpt-4",
      temperature=0.8,
  )
  response = chat_completion.choices[0].message.content
  assert(response)
  return response
  
if __name__ == '__main__':
  file_name = '/tmp/training.txt'
  FACTS = ['Tom works at Block as an ML engineer', 'Tom has a dog named Rocky']
  
  
  for i in tqdm(range(5)):
    for f in FACTS:
      with open(file_name, 'a') as f:
        f.write(get_response(f))
        f.write('\n')