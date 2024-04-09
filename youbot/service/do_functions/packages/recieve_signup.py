from youbot import ENGINE, SIGNUPS


def handle_form_submission(args):
    name = args.get('name')
    phone_number = args.get('phone_number')
    discord_username = args.get('discord_username')
    
    
    with ENGINE.connect() as conn:
        conn.execute(SIGNUPS.insert().values(name=name, phone_number=phone_number, discord_username=discord_username))

    return 'Form submitted with name: {}, phone number: {}, and Discord username: {}'.format(name, phone_number, discord_username)
