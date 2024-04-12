#!/bin/bash -ue
pwd
env
mkdir -p $HOME/.memgpt/functions
cat << EOF > $HOME/.memgpt/credentials
[openai]
auth_type = bearer_token
key = $(echo $OPENAI_API_KEY)
EOF

cp $HOME/youbot/memgpt_extensions/functions/*py $HOME/.memgpt/functions

pip install -r requirements.txt
python script/configure_memgpt.py