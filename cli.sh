# /env/bash

#check if docker is NOT running
if ! curl -s --unix-socket /var/run/docker.sock http/_ping 2>&1 >/dev/null; then
    echo "Docker daemon is not running, please start it to run YouBot!"
    exit 1
fi

# start container in background
docker-compose up -d


SERVICE_NAME="youbot"

# Function to check container status
is_container_running() {
  docker-compose ps -q $SERVICE_NAME | xargs docker inspect -f '{{.State.Running}}' | grep true > /dev/null 2>&1
}

until is_container_running; do
  echo "Waiting for $SERVICE_NAME to start..."
  sleep 1
done

docker-compose attach $SERVICE_NAME