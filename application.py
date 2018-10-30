from personalcapital import PersonalCapital, RequireTwoFactorException, TwoFactorVerificationModeEnum

import getpass
import json
import logging
import os

from cs50 import SQL
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd
from update import get_accounts, get_txs, update_accounts, update_txs

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///budget.db")

# Configure API
pc = PersonalCapital()

@app.route("/")
@login_required
def index():
    """Display the user's accounts and recent transactions"""

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

    totals = {
        'bank_total' : 0.00,
        'retirement_total' : 0.00,
        'cc_total' : 0.00
    }

    for i in accounts:
        bal = float(i['balance'])

        if i['acc_group'] == 'BANK':
            totals['bank_total'] += bal
        elif i['acc_group'] == 'RETIREMENT' or i['acc_group'] == 'INVESTMENT':
            totals['retirement_total'] += bal
        elif i['acc_group'] == 'CREDIT_CARD':
            totals['cc_total'] += bal

        i['balance'] = usd(i['balance'])
        i['updated'] = datetime.utcfromtimestamp(i['updated']/1000).strftime('%Y-%m-%d %H:%M:%S UTC')

    totals['net_worth'] = totals['bank_total'] + totals['retirement_total'] - totals['cc_total']

    for key in totals:
        totals[key] = usd(totals[key])

    transactions = db.execute("SELECT amount, is_credit, date, item, long_item, name \
                                FROM txs \
                                INNER JOIN items \
                                    ON txs.item_id = items.item_id \
                                INNER JOIN accounts \
                                    ON txs.acc_id = accounts.acc_id \
                                WHERE user_id=:user_id \
                                ORDER BY date DESC \
                                LIMIT 30", \
                                user_id=session['user_id'])

    for i in transactions:
        if i['is_credit'] == "True":
            i['amount'] = usd(i['amount'])
        else:
            i['amount'] = usd(-1 * i['amount'])
        i['item'] = (i['item'][:50] + '...') if len(i['item']) > 50 else i['item']

    return render_template("index.html", accounts=accounts, totals=totals, transactions=transactions)

@app.route("/authenticate", methods=["GET","POST"])
@login_required
def authenticate():
    """Authenticate an SMS 2-factor code & update database"""

    # Via POST:
    if request.method == "POST":

        if not request.form.get('sms').isdigit():
            return apology("Please enter valid SMS code")

        # SMS authentication
        pc.two_factor_authenticate(TwoFactorVerificationModeEnum.SMS, request.form.get('sms'))
        pc.authenticate_password(session['password'])

        # Fetch accounts and transactions
        accounts = get_accounts(pc)
        if not accounts or accounts['spHeader']['success'] == False:
            return apology("Error loading accounts", 400)
        update_accounts(accounts, db)

        transactions = get_txs(pc)
        if not transactions or transactions['spHeader']['success'] == False:
            return apology("Error loading transactions", 400)
        update_txs(transactions, db)

        # Let user categorize new transactions
        return redirect("/categorize")

    # Via GET:
    else:
        return render_template("authenticate.html")

@app.route("/business")
@login_required
def business():
    """Display business expenses"""
    return render_template("history.html")

@app.route("/categorize")
@login_required
def categorize():
    """Allow user to categorize spending"""

    return render_template("categorize.html")

@app.route("/history")
@login_required
def history():
    """Display transaction history"""
    return render_template("history.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["pwhash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/monthly")
@login_required
def monthly():
    """Show monthly categorized spending"""
    return render_template("monthly.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username!", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Missing password!", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("Missing password confirmation!", 400)

        # Check match between password and confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and confirmation don't match :(", 400)

        # Hash the password
        hash = generate_password_hash(request.form.get("password"))

        # Add username to database
        result = db.execute("SELECT * FROM users WHERE username = :username", \
                          username=request.form.get("username"))

        if result:
            return apology("Username already exists", 400)

        if not result:
            db.execute("INSERT INTO users (username, pwhash) VALUES(:username, :hash) \)",
                        username=request.form.get("username"),
                        hash=hash)

        # Start session with new user id
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update database with data from API"""

    # Via post:
    if request.method == "POST":

        # Ensure user entered email
        if not request.form.get("pc_email"):
            return apology("Please enter username", 400)

        # Ensure user entered password
        elif not request.form.get("pc_password"):
            return apology("Please enter password", 400)

        # Save email & password to session for use in other routes
        session['email'] = request.form.get("pc_email")
        session['password'] = request.form.get("pc_password")

        # Try to log in
        try:
            pc.login(session['email'], session['password'])

        # If 2-factor is required, send sms & redirect
        except RequireTwoFactorException:
            pc.two_factor_challenge(TwoFactorVerificationModeEnum.SMS)
            return redirect("/authenticate")

        # Fetch accounts and transactions
        else:
            accounts = get_accounts(pc)

            if not accounts or accounts['spHeader']['success'] == False:
                return apology("Error loading accounts", 400)

            update_accounts(accounts, db)

            transactions = get_txs(pc)

            if not transactions or transactions['spHeader']['success'] == False:
                return apology("Error loading transactions", 400)

            update_txs(transactions, db)

        return redirect("/")

    else:
        return render_template("update.html")