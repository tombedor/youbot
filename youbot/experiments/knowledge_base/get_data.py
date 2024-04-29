from youbot.store import Store


docs = Store().get_archival_messages()  # [:MESSAGES_COUNT]

with open('data.txt', 'w') as f:
    for doc in docs:
        f.write(doc + '\n')