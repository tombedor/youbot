import logging
import os
from celery import Celery

from youbot.data_models import YoubotUser
from youbot.clients.twilio_client import send_message
from youbot.knowledge_base.knowledge_base import PrecursorEntFacts, calculate_entity, calculate_ents_facts, get_all_facts
from youbot.memory import is_context_refresh_needed, refresh_context
from youbot.messenger import user_message
from youbot.store import get_pending_reminders, get_youbot_user_by_id, update_reminder_state, upsert_memory_entity


app = Celery("youbot", broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])
app.conf.update(
    task_serializer="pickle",
    accept_content=["pickle"],  # Specify other content types here as well if needed
    task_default_retry_delay=30,  # in seconds
    task_max_retries=3,
    task_ignore_result=True,
)


@app.on_after_configure.connect  # type: ignore
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, process_pending_reminders.s(), name="Reminder check every 60 seconds")  # type: ignore


@app.task
def process_pending_reminders():
    due_reminders = get_pending_reminders()

    if len(due_reminders) > 0:
        logging.info(f"Processing {len(due_reminders)} reminders")

    for reminder in due_reminders:
        youbot_user = get_youbot_user_by_id(reminder.youbot_user_id)
        response = user_message(youbot_user=youbot_user, msg=reminder.reminder_message)
        send_message(message=response, receipient_phone=youbot_user.phone)
        reminder.state = "sent"
        update_reminder_state(reminder.id, "complete")
        refresh_context_async.delay(youbot_user)  # type: ignore


# covers both sms and whatsapp
@app.task
def response_to_twilio_message(youbot_user: YoubotUser, sender_number: str, received_msg: str):
    if sender_number.startswith("whatsapp:"):
        channel = "WhatsApp"
    else:
        channel = "SMS"
    message = f"[the following was sent via {channel}, keep responses brief]: {received_msg}"
    response = user_message(youbot_user=youbot_user, msg=message)
    send_message(message=response, receipient_phone=sender_number)
    refresh_context_async.delay(youbot_user)  # type: ignore


@app.task
def refresh_entity(ent_fact: PrecursorEntFacts):
    entity = calculate_entity(ent_fact)
    if entity:
        upsert_memory_entity(
            youbot_user=ent_fact.youbot_user, entity_name=entity.entity_name, entity_label=entity.entity_label.name, text=entity.summary
        )


@app.task
def refresh_entities(youbot_user: YoubotUser):
    facts = get_all_facts(youbot_user)
    for precursor_ent_fact in calculate_ents_facts(youbot_user, facts):
        refresh_entity.delay(precursor_ent_fact)  # type: ignore


@app.task
def refresh_context_async(youbot_user: YoubotUser):
    if is_context_refresh_needed(youbot_user):
        refresh_context(youbot_user)
        refresh_entities.delay(youbot_user)  # type: ignore
