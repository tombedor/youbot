from typing import Literal
from flask import Flask, jsonify, request
from flask.wrappers import Response

from youbot import ENGINE, SIGNUPS

# start with: gunicorn -w 4 function_handler:app

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world() -> tuple[Response, Literal[200]]:
    return jsonify({"message": "Hello, World!"}), 200

@app.route("/signup", methods=["POST"])
def signup(name: str, phone_number: str, discord_username: str) -> tuple[Response, Literal[200]] | tuple[Response, Literal[500]]:
    # create SIGNUP
    with ENGINE.connect() as conn:
        conn.execute(
            SIGNUPS.insert().values(
                name=name,
                phone_number=phone_number,
                discord_username=discord_username,
            )
        )
        row = conn.execute(SIGNUPS.select().where(SIGNUPS.c.phone_number == phone_number)).fetchone()
        if row:
            return jsonify({"message": "Signup successful", "signup": dict(row)}), 200
        else:
            return jsonify({"message": "Signup failed"}), 500
        

