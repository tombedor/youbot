from youbot.memgpt_extensions.functions.reminder import enqueue_reminder
from youbot.store import get_pending_reminders
from youbot.workers.worker import add, app, process_pending_reminders
from tests import test_user
from celery.contrib.testing.worker import start_worker


class AgentStateStub:
    id = test_user.memgpt_agent_id
    pass


class AgentStub:
    state = AgentStateStub()

    pass


setattr(AgentStub, "enqueue_reminder", enqueue_reminder)


def test_celery():
    # Start up a worker (in LOCAL mode)
    with start_worker(app, perform_ping_check=False):
        # Create and dispatch the task
        task = add.delay(4, 4)  # type: ignore

        # Now let's "work" the task and make sure it executes successfully
        task.get()

        # Verify the task has been executed
        assert task.result == 8
        assert task.state == "SUCCESS"


def test_reminder():
    process_pending_reminders()

    agent = AgentStub()
    agent.enqueue_reminder(year=1999, month=1, day=1, hour=1, minute=1, timezone_name="US/Pacific", message="hello world")  # type: ignore

    assert len(get_pending_reminders()) == 1

    process_pending_reminders()

    assert len(store.get_pending_reminders()) == 0
