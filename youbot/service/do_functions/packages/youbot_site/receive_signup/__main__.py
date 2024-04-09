def handle_form_submission(args):
    name = args.get('name')
    phone_number = args.get('phone_number')
    discord_username = args.get('discord_username')

    return 'Form submitted with name: {}, phone number: {}, and Discord username: {}'.format(name, phone_number, discord_username)
