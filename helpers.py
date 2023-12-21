import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
from flask import redirect, render_template, session
from functools import wraps


def engineer_login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        if session.get("status") != "engineer" and session.get("status") != "master":
            return apology("user does not have privileges for this page", 400)
        return f(*args, **kwargs)

    return decorated_function


def admin_login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        if session.get("status") != "admin" and session.get("status") != "master":
            return apology("user does not have privileges for this page", 400)
        return f(*args, **kwargs)

    return decorated_function


def master_login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        if session.get("status") != "master":
            return apology("user does not have privileges for this page", 400)
        return f(*args, **kwargs)

    return decorated_function
