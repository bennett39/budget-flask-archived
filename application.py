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

from helpers import apology, get_accounts, get_txs, login_required, usd
from update import api_accounts, api_txs, update_accounts, update_txs

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

    # Get accounts and totals from database
    accounts = get_accounts(db)
    if not accounts:
        return apology("Error loading accounts from database", 400)
    else:
        totals = accounts[1]
        accounts = accounts[0]

    # Get transactions from database
    transactions = get_txs(db)
    if not transactions:
        return apology("Error loading transactions", 400)

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
        accounts = api_accounts(pc)
        if not accounts or accounts['spHeader']['success'] == False:
            return apology("Error loading accounts", 400)
        update_accounts(accounts, db)

        transactions = api_txs(pc)
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

@app.route("/categorize", methods=["GET", "POST"])
# @login_required
def categorize():
    """Allow user to categorize spending"""

    session['user_id'] = 1 # REMOVE!!!

    if request.method == "POST":

        result = request.form.to_dict()

        for key in result:
            db.execute("UPDATE txs \
                        SET cat_id=:cat_id \
                        WHERE tx_id=:tx_id",
                        cat_id=int(result[key]),
                        tx_id=int(key))

        return redirect("/")

    # Via GET
    else:
        categories = db.execute("SELECT cat_id, category \
                                 FROM categories")

        # Get transactions from database
        transactions = get_txs(db)
        for i in transactions:
            i['amount'] = usd(i['amount'])

        return render_template("categorize.html", categories=categories, transactions=transactions)

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
# @login_required
def monthly():
    """Show monthly categorized spending"""
    session['user_id'] = 1 # REMOVE!!!

    # Get txs from database
    transactions = get_txs(db)

    # Start months dictionary for all data
    months = {}

    for i in transactions:
        # date comes in as a string, parse it and then format as year-month
        i['date'] = datetime.strptime(i['date'], '%Y-%m-%d').strftime('%Y-%m')

        # Handling negative transactions
        if i['is_credit'] == "True":
            i['amount'] = i['amount']
        else:
            i['amount'] = (-1 * i['amount'])

        # Transaction is start of new month, add month to dictionary as a sub-dictionary
        if i['date'] not in months:
            months[i['date']] = {'total': i['amount']}
        else:
            months[i['date']]['total'] += i['amount']

        # Transaction is start of new category, add category to that month's sub-dictionary
        if i['cat_id'] not in months[i['date']]:
            months[i['date']][i['cat_id']] = i['amount']
        else:
            months[i['date']][i['cat_id']] += i['amount']

    # USD formatting
    for m in months:
        for cat in months[m]:
            months[m][cat] = usd(months[m][cat])

    past = list(months.keys())
    past.reverse()

    categories = db.execute("SELECT cat_id, category \
                                 FROM categories")

    return render_template("monthly.html", months=months, past=past, categories=categories)


@app.route("/profile")
@login_required
def profile():
    """Display user profile - password update and delete account"""
    return render_template("profile.html")


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

    # Via POST:
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
            accounts = api_accounts(pc)
            if not accounts or accounts['spHeader']['success'] == False:
                return apology("Error loading accounts", 400)
            update_accounts(accounts, db)

            transactions = api_txs(pc)
            if not transactions or transactions['spHeader']['success'] == False:
                return apology("Error loading transactions", 400)
            update_txs(transactions, db)

        return redirect("/categorize")

    # Via GET:
    else:
        return render_template("update.html")