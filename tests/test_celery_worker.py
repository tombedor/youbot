from youbot.workers.celery_worker import add, app
from celery.contrib.testing.worker import start_worker


def test_celery():
    # Start up a worker (in LOCAL mode)
    with start_worker(app, perform_ping_check=False):
        # Create and dispatch the task
        task = add.delay(4, 4)

        # Now let's "work" the task and make sure it executes successfully
        task.get()

        # Verify the task has been executed
        assert task.result == 8
        assert task.state == "SUCCESS"
