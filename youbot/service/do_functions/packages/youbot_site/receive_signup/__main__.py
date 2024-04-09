def main(event, context):
    name = event.get('name')
    phone_number = event.get('phone_number')
    discord_username = event.get('discord_username')

    return {
        'msg': 'Form submitted',
        'name': name,
        'phone_number': phone_number,
        'discord_username': discord_username,
    }
   
