import logging
import os
from celery import Celery
from toolz import pipe

from youbot.clients.twilio_client import deliver_twilio_message, prepend_message_length_warning
from youbot.messenger import context_refresh, get_ai_reply
from youbot.prompts import USER_HIDDEN_MSG_PREFIX
from youbot.store import (
    get_pending_reminders,
    get_youbot_user_by_id,
    update_reminder_state,
)
from youbot.system_context import is_context_refresh_needed


app = Celery("youbot", broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])
app.conf.update(
    task_default_retry_delay=30,  # in seconds
    task_max_retries=3,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
)


# @app.on_after_configure.connect  # type: ignore
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(60.0, process_pending_reminders.s(), name="Reminder check every 60 seconds")  # type: ignore


@app.task
def process_pending_reminders():
    due_reminders = get_pending_reminders()

    if len(due_reminders) > 0:
        logging.info(f"Processing {len(due_reminders)} reminders")

    for reminder in due_reminders:
        youbot_user = get_youbot_user_by_id(reminder.youbot_user_id)
        pipe(
            reminder,
            lambda reminder: USER_HIDDEN_MSG_PREFIX + reminder.reminder_message,
            prepend_message_length_warning,
            get_ai_reply(youbot_user),
            deliver_twilio_message(youbot_user.phone),
        )
        update_reminder_state(reminder.id, "complete")
        context_refresh_async.delay(reminder.youbot_user_id)  # type: ignore


# covers both sms and whatsapp
@app.task
def response_to_twilio_message(youbot_user_id: int, sender_number: str, received_msg: str):
    pipe(
        received_msg,
        prepend_message_length_warning,
        get_ai_reply(youbot_user_id),
        deliver_twilio_message(sender_number),
    )
    context_refresh_async.delay(youbot_user_id)  # type: ignore


@app.task
def context_refresh_async(youbot_user_id: int):
    if is_context_refresh_needed(youbot_user_id):
        logging.info(f"Refreshing context for user id {youbot_user_id}")
        context_refresh(youbot_user_id)
