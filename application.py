import getpass
import json
import logging
import os

from cs50 import SQL
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from personalcapital import PersonalCapital, RequireTwoFactorException, TwoFactorVerificationModeEnum
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

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
pc_email = ""
pc_password = ""

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/authenticate", methods=["GET","POST"])
@login_required
def authenticate():
    pass

    # TODO

    # Via POST:
    if request.method == "POST":

        # Get code and complete login
        try:
            pc.two_factor_authenticate(TwoFactorVerificationModeEnum.SMS, request.form.get("sms"))
            pc.authenticate_password(pc_password)
        except:
            return apology("Error executing authentication.", 400)

        # Save response from accounts
        accounts_response = pc.fetch('/newaccount/getAccounts')
        accounts = accounts_response.json()['spData']

        # Ensure response from accounts
        if not accounts_response or not accounts:
            return apology("No response from Personal Capital for that account.", 400)

        # TODO - Save response from transactions

        # TODO - Ensure response from transactions

        # TODO - Update database tables

        # Redirect to "/"
        return redirect("/")

    # Via GET, render authenticate.html
    else:
        render_template("authenticate.html")


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
        result = db.execute("INSERT INTO users (username, pwhash) VALUES(:username, :hash)",
                            username=request.form.get("username"),
                            hash=hash)

        # Apologize if username already exists
        if not result:
            return apology("Username already exists", 400)

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

    if request.method == "POST":

        if not request.form.get("pc_email"):
            return apology("Please enter username", 400)

        elif not request.form.get("pc_password"):
            return apology("Please enter password", 400)

        pc_email = request.form.get("pc_email")
        pc_password = request.form.get("pc_password")

        try:
            pc.login(pc_email, pc_password)
        except RequireTwoFactorException:
            pc.two_factor_challenge(TwoFactorVerificationModeEnum.SMS)
            return render_template("authenticate.html")
        except:
            return apology("Something went wrong logging in.", 400)
        else:
            # Save response from accounts
            accounts_response = pc.fetch('/newaccount/getAccounts')
            accounts = accounts_response.json()['spData']

            # Ensure response from accounts
            if not accounts_response or not accounts:
                return apology("No response from Personal Capital for that account.", 400)

            # TODO - Save response from transactions

            # TODO - Ensure response from transactions

            # TODO - Update database

            return redirect("/")

    else:
        return render_template("update.html")