#!/bin/bash
set -ex

# note: expects OPENAI_API_TOKEN and DIGITAL_OCEAN_TOKEN to be available 
# (for vscode container, use codespace secrets)

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
sudo -u root sudo -u postgres nohup /usr/lib/postgresql/12/bin/postgres -D /var/lib/postgresql/12/main -c config_file=/etc/postgresql/12/main/postgresql.conf > /tmp/nohup.out &

sudo -u root sudo -u postgres psql -c "CREATE USER youbot WITH PASSWORD 'youbot';"
sudo -u root sudo -u postgres psql -c "CREATE DATABASE youbot;"
sudo -u root sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE youbot TO youbot;"

####### install dependencies #######
poetry config virtualenvs.in-project true
poetry install

###### memgpt setup #######
mkdir -p /home/$USER/.memgpt

cat << EOF > /$HOME/.memgpt/credentials
[openai]
auth_type = bearer_token
key = $(echo $OPENAI_API_KEY)
EOF


##### install digital ocean tools #####
# if DIGITAL_OCEAN_TOKEN is available, install and configure doctl
if [ -n "$DIGITAL_OCEAN_TOKEN" ]; then
    pushd .
    cd $HOME
    wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz
    tar xf ~/doctl-1.104.0-linux-amd64.tar.gz
    sudo mv $HOME/doctl /usr/local/bin

    doctl completion bash >> $HOME/.bash_profile
    source $HOME/.bash_profile

    doctl auth init -t $DIGITAL_OCEAN_TOKEN
    popd
fi

####### setup aliases #######

cat << EOF >> $HOME/.bash_profile
export POSTGRES_URL="postgresql://youbot:youbot@localhost/youbot"
export MEMGPT_CONFIG_PATH="/workspaces/youbot/config/memgpt_config"
alias youbot="poetry run memgpt run --agent youbot --persona sam_pov --human basic --first --debug"
EOF