import getpass
import json
import logging
import os
import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import redirect, render_template, request, session
from functools import wraps
from personalcapital import PersonalCapital


def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", code=code, message=message), code

def get_accounts(pc):
    """
    Fetch accounts data from Personal Capital API

    https://github.com/haochi/personalcapital
    """
    accounts_response = pc.fetch('/newaccount/getAccounts')
    return accounts_response.json()


def get_txs(pc):
    """
    Fetch transaction data from Personal Capital API

    https://github.com/haochi/personalcapital
    """
    now = datetime.now()
    date_format = '%Y-%m-%d'
    days = 90
    start_date = (now - (timedelta(days=days+1))).strftime(date_format)
    end_date = (now - (timedelta(days=1))).strftime(date_format)
    transactions_response = pc.fetch('/transaction/getUserTransactions', {
        'sort_cols': 'transactionTime',
        'sort_rev': 'true',
        'page': '0',
        'rows_per_page': '100',
        'startDate': start_date,
        'endDate': end_date,
        'component': 'DATAGRID'
    })

    return transactions_response.json()


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"