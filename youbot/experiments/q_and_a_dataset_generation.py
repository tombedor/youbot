import subprocess

from openai import OpenAI


subprocess.run("""psql $POSTGRES_URL -c "SELECT text FROM memgpt_archival_memory_agent" --tuples-only > /tmp/archival.txt""", shell=True)


import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test in json format",
        }
        
    ],
    model="gpt-4-turbo-preview",
    temperature=0.7,
    response_format = { "type": "json_object" }
)
print('foo')
        
    #   ]
      
    # )
    #     # prompt=prompt,
    #     # max_tokens=1024,
    #     # temperature=0.9,
    #     # top_p=1,
    #     # frequency_penalty=0.0,
    #     # presence_penalty=0.0
    # )

with open('/tmp/archival.txt', 'r') as f:
    lines = f.readlines()


for line in lines:
    print(f"LINE IS {line}")



template = """
"As an understanding language model, your mission is to
construct ten unique pairs of conversational sentences
representing the same fact - 'Tom is engaged to Justina.' Each
pair should comprise a question and an appropriate response that
naturally divulges the information.

Arrange your output in a JSON array, with each item being a
dictionary containing a 'PROMPT' and 'LABEL'. The 'PROMPT' is
the crafted question and the 'LABEL' is its corresponding
answer.

Remember, every question-answer pair should provide a fresh
perspective while efficiently conveying 'Tom is engaged to
Justina.' Let's see how creative and diverse the dialogue can
be."
"""

response = openai.Completion.create(
  engine='text-davinci-002',
  prompt='Translate the following English text to French: \'',
  max_tokens=60
)