import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", code=code, message=message), code

def get_accounts(db):
    """Get accounts from database"""
    # Get accounts from database
    # Last time account was updated = 'updated'
    accounts = db.execute("SELECT name, acc_type, acc_group, balance, updated, institution \
                            FROM accounts \
                            INNER JOIN ( \
                                SELECT balances.acc_id, balance, updated \
                                FROM balances \
                                INNER JOIN ( \
                                    SELECT acc_id, max(time) AS updated \
                                    FROM balances \
                                    GROUP BY acc_id \
                                ) AS temp \
                                ON balances.acc_id = temp.acc_id \
                                GROUP BY balances.acc_id \
                            ) AS current \
                            ON accounts.acc_id = current.acc_id \
                            INNER JOIN institutions \
                            ON institutions.institution_id = accounts.institution_id \
                            WHERE user_id=:user_id \
                            ORDER BY institution", \
                            user_id=session['user_id'])

    # Initialize dictionary of account type sums
    totals = {
        'bank_total' : 0.00,
        'retirement_total' : 0.00,
        'cc_total' : 0.00
    }

    # Update account type sums
    for i in accounts:
        bal = float(i['balance'])

        if i['acc_group'] == 'BANK':
            totals['bank_total'] += bal
        elif i['acc_group'] == 'RETIREMENT' or i['acc_group'] == 'INVESTMENT':
            totals['retirement_total'] += bal
        elif i['acc_group'] == 'CREDIT_CARD':
            totals['cc_total'] += bal

        # After addition, format as USD strings
        i['balance'] = usd(i['balance'])

        # Time last updated, UNIX to UTC conversion
        i['updated'] = datetime.utcfromtimestamp(i['updated']/1000).strftime('%Y-%m-%d %H:%M:%S UTC')

    # Calculate net worth
    totals['net_worth'] = totals['bank_total'] + totals['retirement_total'] - totals['cc_total']

    # Format as USD string
    for key in totals:
        totals[key] = usd(totals[key])

    return [accounts, totals]


def get_txs(db):
    """Get transactions from database"""
    # Get transactions from database
    transactions = db.execute("SELECT tx_id, amount, txs.cat_id, category, cat_group, is_credit, date, item, name \
                                FROM txs \
                                INNER JOIN items \
                                    ON txs.item_id = items.item_id \
                                INNER JOIN accounts \
                                    ON txs.acc_id = accounts.acc_id \
                                LEFT JOIN categories \
                                    ON txs.cat_id = categories.cat_id \
                                WHERE user_id=:user_id \
                                ORDER BY date DESC", \
                                user_id=session['user_id'])


    for i in transactions:

        # Create negative numbers
        if i['is_credit'] == "True":
            i['amount'] = i['amount']
        else:
            i['amount'] = -1 * i['amount']

        # Truncate description strings
        i['item'] = (i['item'][:50] + '...') if len(i['item']) > 50 else i['item']

    return transactions


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
    if value >= 0:
        return f"$ {value:,.2f}"
    else:
        return f"($ {value:,.2f})"