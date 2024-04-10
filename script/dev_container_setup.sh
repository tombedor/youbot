#!/bin/bash
set -ex

####### install postgres #######

# updating package list and installing some utilities
sudo apt-get update && sudo apt-get install -y wget gnupg

# adding PostgreSQL's official apt repository
sudo echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# importing the repository signing key
sudo wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# updating the package list and install postgresql
sudo apt-get update && sudo apt-get -y install postgresql-12

# starting postgres
sudo -u root sudo -u postgres /usr/lib/postgresql/12/bin/postgres -D /var/lib/postgresql/12/main -c config_file=/etc/postgresql/12/main/postgresql.conf

sudo -u root sudo -u postgres psql -c "CREATE USER youbot WITH PASSWORD 'youbot';"
sudo -u root sudo -u postgres psql -c "CREATE DATABASE youbot;"
sudo -u root sudo -u postgres psql -c "GRANT ALL PERMISSIONS ON DATABASE youbot TO youbot;"

export POSTGRES_URL="postgresql://youbot:youbot@localhost/youbot"
export MEMGPT_CONFIG_PATH="/workspaces/youbot/config/memgpt_config"

alias youbot="poetry run memgpt run --agent youbot --persona sam_pov --human basic --first --debug"

mkdir -p /home/$USER/.memgpt

cat << EOF > /$HOME/.memgpt/credentials
[openai]
auth_type = bearer_token
key = $(echo $OPENAI_API_KEY)
EOF

####### install dependencies #######
poetry install