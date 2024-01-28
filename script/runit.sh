#!/env/bin/bash

# something broken about this

exec 2>&1
cd /root/MemGPT-Extensions
exec poetry run python client/discord_tombot.py