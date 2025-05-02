import sqlite3
import hashlib
import uuid
import logging
from common.gen_utils import Response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = sqlite3.connect("data/server.db")
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (uuid VARCHAR, username VARCHAR, pswdhash VARCHAR)")

class User:
    def __init__(self, username: str):
        """-- Do not use this method. Use User.new() to create a user and register it. --
        Create a new User class with no authentication methods."""
        self.uuid = uuid.uuid1()
        self.name = username
        Response(True, f"Initialized User instance for username: {username}")

    @classmethod
    def check_username_available(cls, username: str) -> bool:
        logging.debug("Checking if username '%s' exists in the database.", username)
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return Response(False, f"Username {username} exists")
        else:
            return Response(True, f"Username {username} does not exist.")

    @classmethod
    def register(cls, username: str, password: str):
        """Register a user using username and password"""
        logging.debug("Attempting to register user with username: %s", username)
        if not cls.check_username_available(username):
            return Response(False, "Username taken")

        user = cls(username)
        user.pswdhash = hashlib.sha256(password.encode()).hexdigest()

        cur.execute("INSERT INTO users VALUES (?, ?, ?)", (str(user.uuid), user.name, user.pswdhash))
        db.commit()

        logging.info(f"User {username} registered successfully")
        return Response(True, "Registered")

    @classmethod
    def login(cls, username: str, password: str):
        """Login a user using username and password"""
        cur.execute("SELECT * FROM users WHERE username = ? AND pswdhash = ?", (username, hashlib.sha256(password.encode()).hexdigest()))
        resp = cur.fetchone()
        if resp:
            user = cls(resp[1])
            user.uuid = resp[0]
            user.pswdhash = resp[2]

            logging.info(f"User {username} logged in")
            return Response(True, "Logged in")
        else:
            logging.info(f"User {username} failed to log in")
            return Response(False, "Incorrect username or password")
