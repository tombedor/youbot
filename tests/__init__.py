import os

from youbot.onboard_user import onboard_user
from youbot.store import get_youbot_user_by_phone

# see: https://www.twilio.com/docs/iam/test-credentials#test-sms-messages

os.environ["TWILIO_ACCOUNT_SID"] = os.environ["TWILIO_TEST_ACCOUNT_SID"]
os.environ["TWILIO_AUTH_TOKEN"] = os.environ["TWILIO_TEST_AUTH_TOKEN"]
os.environ["TWILIO_SENDER_NUMBER"] = "+15005550006"
TEST_RECIPIENT = "+14153231234"


os.environ["DATABASE_URL"] = "postgresql://localhost:8888/memgpt?user=memgpt&password=memgpt"

try:
    onboard_user(phone=TEST_RECIPIENT, human_name="John Doe", human_description="a test user")
except ValueError:
    pass
    # expected


test_user = get_youbot_user_by_phone(TEST_RECIPIENT)
