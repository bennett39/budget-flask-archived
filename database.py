from cs50 import SQL
from flask import redirect, render_template, request, session

def update_accounts(accounts, db):
    for i in accounts['spData']['accounts']:
        # Update institutions
        institution_id = db.execute("SELECT institution_id FROM institutions WHERE institution=:institution", \
                           institution=i['firmName'])
        if not institution_id:
            db.execute("INSERT INTO institutions (institution) VALUES(:institution)", \
                        institution=i['firmName'])
            institution_id = db.execute("SELECT institution_id FROM institutions WHERE institution=:institution", \
                                        institution=i['firmName'])

        # Update accounts
        acc_id = db.execute("SELECT acc_id FROM accounts WHERE pc_accountid=:pc_accountid", \
                             pc_accountid=i['accountId'])
        if not acc_id:
            db.execute("INSERT INTO accounts (pc_accountid, name, acc_type, institution_id, acc_group, user_id) \
                        VALUES(:pc_accountid, :name, :acc_type, :institution_id, :acc_group, :user_id)", \
                        pc_accountid=i['accountId'],
                        name=i['name'],
                        acc_type=i['accountType'],
                        institution_id=institution_id[0]['institution_id'],
                        acc_group=i['accountTypeGroup'],
                        user_id=session['user_id'])

            acc_id = db.execute("SELECT acc_id FROM accounts WHERE pc_accountid=:pc_accountid", \
                                 pc_accountid=i['accountId'])

        # Update balances
        bal_id = db.execute("SELECT bal_id FROM balances WHERE time=:time AND acc_id=:acc_id", \
                             time=i['lastRefreshed'],
                             acc_id=acc_id[0]['acc_id'])
        if not bal_id:
            db.execute("INSERT INTO balances (acc_id, balance, time) \
                        VALUES(:acc_id, :balance, :time)", \
                        acc_id=acc_id[0]['acc_id'],
                        balance=i['balance'],
                        time=i['lastRefreshed'])
            bal_id = db.execute("SELECT bal_id FROM balances WHERE time=:time", \
                             time=i['lastRefreshed'])


def update_txs(transactions, db):
    for i in transactions['spData']['transactions']:
        # Update items
        item_id = db.execute("SELECT item_id FROM items WHERE item=:item", \
                              item=i['description'])

        if not item_id:
            db.execute("INSERT INTO items (item, long_item) \
                        VALUES (:item, :long_item)", \
                        item=i['description'],
                        long_item=i['originalDescription'])
            item_id = db.execute("SELECT item_id FROM items WHERE item=:item", \
                                  item=i['description'])

        # Update txs:
        tx_id = db.execute("SELECT tx_id FROM txs WHERE pc_txid=:pc_txid", \
                            pc_txid=i['userTransactionId'])

        if not tx_id:
            acc_id = db.execute("SELECT acc_id FROM accounts WHERE pc_accountid=:pc_accountid", \
                                 pc_accountid=i['accountId'])
            credit_bool = 0
            if i['isCredit'] == 'true':
                credit_bool = 1

            db.execute("INSERT INTO txs (acc_id, item_id, amount, is_credit, pc_catid, date, pc_txid) \
                        VALUES (:acc_id, :item_id, :amount, :is_credit, :pc_catid, :date, :pc_txid)", \
                        acc_id=acc_id[0]['acc_id'],
                        item_id=item_id[0]['item_id'],
                        amount=i['amount'],
                        is_credit=credit_bool,
                        pc_catid=i['categoryId'],
                        date=i['transactionDate'],
                        pc_txid=i['userTransactionId'])