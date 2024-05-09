import logging
import os
from celery import Celery

from youbot.clients.memgpt_client import MemGPTClient
from youbot.clients.twilio_client import send_message
from youbot.store import Store, YoubotUser

app = Celery("youbot", broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])
app.conf.update(
    task_serializer="pickle",
    accept_content=["pickle"],  # Specify other content types here as well if needed
)


@app.on_after_configure.connect  # type: ignore
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, process_pending_reminders.s(), name="add every 10")


@app.task
def process_pending_reminders():
    due_reminders = Store().get_pending_reminders()

    if len(due_reminders) > 0:
        logging.info(f"Processing {len(due_reminders)} reminders")

    for reminder in due_reminders:
        youbot_user = Store().get_youbot_user_by_id(reminder.youbot_user_id)
        response = MemGPTClient.user_message(youbot_user=youbot_user, msg=reminder.reminder_message)
        send_message(message=response, receipient_phone=youbot_user.phone)
        reminder.state = "sent"
        Store().update_reminder_state(reminder.id, "complete")


@app.task
def response_to_sms(youbot_user: YoubotUser, sender_number: str, received_msg: str):
    message = f"[the following was sent via SMS, keep responses brief]: {received_msg}"
    response = MemGPTClient.user_message(youbot_user=youbot_user, msg=message)
    send_message(message=response, receipient_phone=sender_number)


@app.task
def add(x, y):
    return x + y
