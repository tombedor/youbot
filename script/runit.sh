#!/bin/bash

# Step 1: Create the service directory
sudo mkdir -p /etc/sv/youbot

# Step 2: Write the run script for the service
cat <<EOF | sudo tee /etc/sv/youbot/run
#!/bin/sh
# Load environment variables for root
. /root/.profile

# Start the service
cd /root/youbot && poetry run python youbot/service/discord_service.py
EOF

# Step 3: Make the service run script executable
sudo chmod +x /etc/sv/youbot/run

# Step 4: Set up logging for the service
# Create a directory for logs
sudo mkdir -p /etc/sv/youbot/log/main

# Create the log run script
cat <<EOF | sudo tee /etc/sv/youbot/log/run
#!/bin/sh
exec svlogd -tt /etc/sv/youbot/log/main
EOF

# Make the log script executable
sudo chmod +x /etc/sv/youbot/log/run

# Step 5: Link the service to the runit service directory
sudo ln -s /etc/sv/youbot /etc/service/

# Display message
echo "youbot service with logging has been set up. To check its status, run 'sudo sv status youbot'"
