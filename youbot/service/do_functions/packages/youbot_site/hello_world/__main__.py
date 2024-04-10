import os
import requests

# Fetch the IP from the environment variable
ip_address = os.getenv('DROPLET_IP')

# Create the URL, assuming the prefix is http
url = f'https://{ip_address}/hello_world'

# Make the GET request, catch and print any request exception
try:
    response = requests.get(url)
    response.raise_for_status()

    # Print the response if there's no exception
    print(response.text)

except requests.exceptions.RequestException as err:
    print(f'Request failed: {err}')