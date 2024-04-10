
DROPLET_IP=$(doctl compute droplet list --tag-name youbot --format PublicIPv4 --no-header)
doctl serverless deploy $0/../../youbot/service/do_functions