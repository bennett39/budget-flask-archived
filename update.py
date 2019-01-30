from personalcapital import PersonalCapital

import json
import os
from datetime import datetime, timedelta

from cs50 import SQL
from flask import redirect, render_template, request, session

def get_pc_data(pc, data_type):
    payload = create_pc_payload(data_type)
    if payload:
        endpoint = '/transaction/getUserTransactions'
        response = pc.fetch(endpoint, payload)
    else:
        endpoint = '/newaccount/getAccounts'
        response = pc.fetch(endpoint)
    return response.json()


def create_pc_payload(data_type):
    if data_type == 'transactions':
        now = datetime.now()
        date_format = '%Y-%m-%d'
        days = 90
        start_date = (now - (timedelta(days=days+1))).strftime(date_format)
        end_date = (now - (timedelta(days=1))).strftime(date_format)
        return {
            'sort_cols': 'transactionTime',
            'sort_rev': 'true',
            'page': '0',
            'rows_per_page': '100',
            'startDate': start_date,
            'endDate': end_date,
            'component': 'DATAGRID'
        }
    return False


def update_accounts(accounts, db):
    """ Use API accounts data to update database tables """
    for i in accounts['spData']['accounts']:
        # Update institutions
        institution = i['firmName']
        institution_response = db.execute("""SELECT institution_id 
                              FROM institutions
                              WHERE institution=:institution""",\
                              institution=institution)
        if not institution_response:
            db.execute("""INSERT INTO institutions (institution)
                              VALUES(:institution)""", \
                              institution=institution)
            institution_response = db.execute("""SELECT institution_id 
                              FROM institutions 
                              WHERE institution=:institution""",\
                              institution=institution)
        institution_id = institution_response[0]['institution_id']

        # Update accounts
        pc_accountid = i['accountId']
        account_response = db.execute("""SELECT acc_id FROM accounts 
                              WHERE pc_accountid=:pc_accountid""",\
                              pc_accountid=pc_accountid)
        if not account_response:
            db.execute("""INSERT INTO accounts (pc_accountid, name, 
                              acc_type, institution_id, acc_group, user_id)
                              VALUES(:pc_accountid, :name, :acc_type, 
                              :institution_id, :acc_group, :user_id)""",\
                              pc_accountid=pc_accountid,\
                              name=i['name'],\
                              acc_type=i['accountType'],\
                              institution_id=institution_id,\
                              acc_group=i['accountTypeGroup'],\
                              user_id=session['user_id'])
            account_response = db.execute("""SELECT acc_id FROM accounts 
                              WHERE pc_accountid=:pc_accountid""",\
                              pc_accountid=i['accountId'])
        account_id = account_response[0]['acc_id']

        # Update balances
        time = i['lastRefreshed']
        balance_response = db.execute("""SELECT bal_id FROM balances 
                              WHERE time=:time AND acc_id=:account_id""",\
                              time=time,\
                              account_id=account_id)
        if not balance_response:
            db.execute("""INSERT INTO balances (acc_id, balance, time) 
                              VALUES(:account_id, :balance, :time)""",\
                              account_id=account_id,\
                              balance=i['balance'],\
                              time=time)


def update_txs(transactions, db):
    """ Use API transaction data to update database tables """
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

            is_credit = str(i['isCredit'])

            db.execute("INSERT INTO txs (acc_id, item_id, amount, is_credit, pc_catid, date, pc_txid) \
                        VALUES (:acc_id, :item_id, :amount, :is_credit, :pc_catid, :date, :pc_txid)", \
                        acc_id=acc_id[0]['acc_id'],
                        item_id=item_id[0]['item_id'],
                        amount=i['amount'],
                        is_credit=is_credit,
                        pc_catid=i['categoryId'],
                        date=i['transactionDate'],
                        pc_txid=i['userTransactionId'])
