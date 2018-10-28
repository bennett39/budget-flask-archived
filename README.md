# budget

This web app takes data from a Personal Capital API to build a custom budget for my income/expenses.

The most recent changes are on the development branch.

## Model:
`budget.db` - includes 7 tables. See `api-db-map.txt` for details.

## View:
The web app uses Jinja and Bootstrap to create dynamic HTML and standard CSS.

*Currently implemented:*
`apology.html`, `index.html`, `layout.html`, `login.html`, `register.html`, `update.html`, `authenticate.html`

*Not yet implemented:*
Complete `index.html`

`history.html`, `monthly.html`, `business.html`, `profile.html`, `update.html`

## Controller
`application.py` runs a Flask server to handle requests and logic
`helpers.py` provides some commonly-used functions
`update.py` contains the functions for requesting from API and adding that data to database
