# budget

This web app takes data from a Personal Capital API to build a custom budget for my income/expenses.

The most recent changes are on the development branch.

## Model:
`budget.db` - Will include six tables:

### Currently implemented:
1. `users`: `user_id`, `username`, `pwhash`, `pc_email`

### Not yet implemented:
2. `accounts`: `acc_id`, `acc_name`
3. `balances`: `bal_id`, `acc_id`, `balance`, `bal_time`
4. `txs`: `tx_id`, `user_id`, `item_id`, `category_id`, `amount`, `is_credit`, `tx_time`
5. `items`: `item_id`, `item`
6. `categories`: `cat_id`, `category`

## View:
The web app uses Jinja and Bootstrap to create dynamic HTML and standard CSS.

### Currently implemented:
`apology.html`, `index.html`, `layout.html`, `login.html`, `register.html`

### Not yet implemented:
Complete index.html

`history.html`, `monthly.html`, `business.html`, `profile.html`

## Controller
A Python application (application.py) runs a Flask server to handle requests.