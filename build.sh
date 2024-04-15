#!/bin/bash -ue
pwd
env

mkdir -p $HOME/.memgpt/

cat << EOF > $HOME/.memgpt/credentials
[openai]
auth_type = bearer_token
key = $(echo $OPENAI_API_KEY)
EOF