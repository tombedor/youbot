from celery import Celery
from celery.schedules import crontab

app = Celery()


@app.on_after_configure.connect # type: ignore
def setup_periodic_tasks(sender, **_):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s("hello"), name="add every 10")  # type: ignore

    # Calls test('hello') every 30 seconds.
    # It uses the same signature of previous task, an explicit name is
    # defined to avoid this task replacing the previous one defined.
    sender.add_periodic_task(30.0, test.s("hello"), name="add every 30")  # type: ignore

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s("world"), expires=10) # type: ignore

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1), # type: ignore
        test.s("Happy Mondays!"), # type: ignore
    )


@app.task
def test(arg):
    print(arg)


@app.task
def add(x, y):
    z = x + y
    print(z)
