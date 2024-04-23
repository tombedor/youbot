import os
from youbot import app
from celery import Celery

app = Celery("youbot", broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])


@app.task
def add(x, y):
    return x + y
