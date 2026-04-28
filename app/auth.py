sessions = {}
import uuid


def login_user(user):
    token = str(uuid.uuid4())
    sessions[token] = user
    return token


def logout_user(token):
    if token in sessions:
        del sessions[token]


def get_current_user(token):
    return sessions.get(token)
