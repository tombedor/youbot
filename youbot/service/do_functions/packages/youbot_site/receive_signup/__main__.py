import logging


def main(event, context):
    print(event)
    print(context)
    name = event.get("name")
    phone_number = event.get("phone_number")
    discord_username = event.get("discord_username")
    honeypot = event.get("url")

    if honeypot:
        logging.warn("Honeypot triggered")
        return {
            "body": {
                "msg": "Form submitted",
                "name": name,
                "phone_number": phone_number,
                "discord_username": discord_username,
            },
            "statusCode": 200,
        }
    else:
        return {
            "body": {
                "msg": "Form submitted",
                "name": name,
                "phone_number": phone_number,
                "discord_username": discord_username,
            },
            "statusCode": 200,
        }
