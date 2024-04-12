# assumes one host and one db, TODO do this with tags?
def setup_database_ssh_tunnel():
    subprocess.run("doctl auth init", shell=True, capture_output=True, text=True)

    response = subprocess.run("doctl compute droplet list --output json", shell=True, capture_output=True, text=True)
    network_infos = json.loads(response.stdout)[0]["networks"]["v4"]
    public_ip = next(entry["ip_address"] for entry in network_infos if entry["type"] == "public")

    response = subprocess.run("doctl databases list --output json", shell=True, capture_output=True, text=True)
    db_connection_info = json.loads(response.stdout)[0]["private_connection"]
    host = db_connection_info["host"]
    port = db_connection_info["port"]

    subprocess.run(f"ssh -N -L {port}:{host}:{port} root@{public_ip}", shell=True, capture_output=True)
    # replace background process
    # TODO: use autossh
