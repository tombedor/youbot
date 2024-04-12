#!/bin/bash -ue
pwd
env
whomai

pip install -r requirements.txt

mkdir -p $HOME/.memgpt/functions

cp /workspace/youbot/memgpt_extensions/functions/*py $HOME/.memgpt/functions

cat << EOF > $HOME/.memgpt/credentials
[openai]
auth_type = bearer_token
key = $(echo $OPENAI_API_KEY)
EOF