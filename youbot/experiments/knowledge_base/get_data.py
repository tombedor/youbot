from pandas import DataFrame
from youbot.store import get_archival_messages


docs = get_archival_messages()  # [:MESSAGES_COUNT]

df = DataFrame(docs)

with open("msgs.pkl", "wb") as f:
    df.to_pickle(f)
