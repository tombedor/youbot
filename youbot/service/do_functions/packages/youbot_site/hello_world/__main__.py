import os
import requests


def main(event, context):
    print(event)
    print(dir(context))
    # Fetch the IP from the environment variable
    ip_address = "MY_IP"

    print(f'IP address: {ip_address}')

    # Create the URL, assuming the prefix is http
    url = f'http://{ip_address}:8000/'
    
    print(url)

    # Make the GET request, catch and print any request exception
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Print the response if there's no exception
        print(response.text)

    except requests.exceptions.RequestException as err:
        print(f'Request failed: {err}')