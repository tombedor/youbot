from hashlib import md5
import subprocess

from openai import OpenAI

from youbot.json_decoder import parse_json
from datasets import Dataset


def retrieve_archival_memories():
  subprocess.run("""psql $POSTGRES_URL -c "SELECT text FROM memgpt_archival_memory_agent" --tuples-only > /tmp/archival.txt""", shell=True)
  with open('/tmp/archival.txt', 'r') as f:
    return f.readlines()
  


import os
from openai import OpenAI


def get_response(fact):
    hash = md5(fact.encode("utf-8")).hexdigest()
    filename = f"/tmp/{hash}"

    if os.path.exists(filename):
        with open(filename) as f:
            return parse_json(f.read())

    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    prompt = f"""
As an understanding language model, your mission is to
construct ten unique pairs of conversational sentences
representing the same fact - '{fact}' Each
pair should comprise a question and an appropriate response that
naturally divulges the information.

Arrange your output in a JSON array, with each item being a
dictionary containing a 'PROMPT' and 'LABEL'. The 'PROMPT' is
the crafted question and the 'LABEL' is its corresponding
answer.

Remember, every question-answer pair should provide a fresh
perspective while efficiently conveying '{fact}' 

Each question and answer should be relatively brief.
"""
<<<<<<< HEAD
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4",
        temperature=0.7,
        # response_format = { "type": "json_object" }
    )
    response = chat_completion.choices[0].message.content
    assert response

    with open(filename, "w") as f:
        f.write(response)
    return parse_json(response)

||||||| parent of 6d4f3d7 (kb)
  chat_completion = client.chat.completions.create(
      messages=[
          {
              "role": "user",
              "content": prompt,
          }
          
      ],
      model="gpt-4",
      temperature=0.7,
      # response_format = { "type": "json_object" }
  )
  response = chat_completion.choices[0].message.content
  assert(response)
  
  with open(filename, 'w') as f:
    f.write(response)
  return parse_json(response)
  
=======
  chat_completion = client.chat.completions.create(
      messages=[
          {
              "role": "user",
              "content": prompt,
          }
          
      ],
      model="gpt-4",
      temperature=0.8,
      # response_format = { "type": "json_object" }
  )
  response = chat_completion.choices[0].message.content
  assert(response)
  
  with open(filename, 'w') as f:
    f.write(response)
  return parse_json(response)
  
>>>>>>> 6d4f3d7 (kb)

def get_data():
    subprocess.run(
        """psql $POSTGRES_URL -c "SELECT text FROM memgpt_archival_memory_agent" --tuples-only > /tmp/archival.txt""", shell=True
    )
    q_and_a = []
    with open("/tmp/archival.txt", "r") as f:
        lines = f.readlines()

    for line in lines:
        fact = line.strip()
        print(fact)
        responses = get_response(fact)
        q_and_a += responses
    return q_and_a
