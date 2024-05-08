#!/bin/bash
set -ex

# note: expects OPENAI_API_TOKEN and DIGITAL_OCEAN_TOKEN to be available
# (for vscode container, use codespace secrets)

####### install postgres #######

# updating package list and installing some utilities
sudo apt-get update && sudo apt-get install -y wget gnupg

# adding PostgreSQL's official apt repository
sudo echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# importing the repository signing key
sudo wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# updating the package list and install postgresql
sudo apt-get update && sudo apt-get -y install postgresql-12

# starting postgres
# this returns even thought the db isn't started yet, hacky bit is to just put the db commands lower in the script
sudo -u root sudo -u postgres nohup /usr/lib/postgresql/12/bin/postgres -D /var/lib/postgresql/12/main -c config_file=/etc/postgresql/12/main/postgresql.conf >/tmp/nohup.out &

### install redis ###

sudo apt-get -y install redis-server
sudo service redis-server start

####### install dependencies #######
poetry config virtualenvs.create false
poetry install

sudo -u root sudo -u postgres psql -c "CREATE USER youbot WITH PASSWORD 'youbot';"
sudo -u root sudo -u postgres psql -c "CREATE DATABASE youbot;"
sudo -u root sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE youbot TO youbot;"
