import pytest
from flask.testing import FlaskClient

from youbot.api import app  # replace with the actual import for your Flask app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_routes(client: FlaskClient):
    assert "health" in app.url_map._rules_by_endpoint.keys()


def test_health_route(client: FlaskClient):
    response = client.get("/health")
    assert response.status_code == 200


# def test_sms_reply():
# post request to /receive_sms route

# response = client.post("/receive_sms", data={"Body": "Hello, World!"})
