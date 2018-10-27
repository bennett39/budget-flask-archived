from cs50 import SQL
from flask import redirect, render_template, request, session

def txs_test():
    return {
    'spHeader':{
        'SP_HEADER_VERSION':-1,
        'userStage':'B',
        'betaTester':False,
        'accountsMetaData':[
            'HAS_ON_US',
            'HAS_CASH',
            'HAS_INVESTMENT',
            'HAS_CREDIT'
        ],
        'success':True,
        'qualifiedLead':False,
        'developer':False,
        'userGuid':'5689dc6f8d874eb59ad1052e162e3cd3',
        'authLevel':'SESSION_AUTHENTICATED',
        'deviceName':' #29',
        'username':'bennettgarner@gmail.com',
        'status':'ACTIVE'
    },
    'spData':{
        'intervalType':'MONTH',
        'endDate':'2018-10-25',
        'moneyIn':10228.97,
        'transactions':[
            {
                'symbol':'',
                'isInterest':False,
                'netCost':0.0,
                'cusipNumber':'',
                'accountName':'Blue Cash Everyday - X2005',
                'description':'Wnyc/wqxr/njpr/nypr Xxxxxx4000 2xxx0804rgxxxxx-xx-04-rg--xxx8730',
                'memo':'',
                'isCredit':False,
                'isEditable':True,
                'isCashOut':True,
                'merchantId':'1W4wINN6CUFA4v0N-xak17Y1DTRNstp-RdWdHZX1Ea4',
                'price':0.0,
                'holdingType':'',
                'lotHandling':'',
                'customReason':'',
                'userTransactionId':5176324116,
                'currency':'USD',
                'isDuplicate':False,
                'resultType':'aggregated',
                'originalDescription':'Wnyc/wqxr/njpr/nypr Xxxxxx4000 2xxx0804rgxxxxx-xx-04-rg--xxx8730',
                'isSpending':True,
                'amount':5.0,
                'checkNumber':'',
                'transactionTypeId':0,
                'isIncome':False,
                'includeInCashManager':True,
                'merchant':'',
                'isNew':False,
                'isCashIn':False,
                'transactionDate':'2018-08-04',
                'transactionType':'Debit',
                'accountId':'10003703_12495704_48433256',
                'originalAmount':5.0,
                'isCost':False,
                'userAccountId':48433256,
                'simpleDescription':'Wnyc/wqxr/njpr/nypr Xx4000 2xx0804rgxx-04-rg--xx8730',
                'catKeyword':'Wnyc Wqxr',
                'runningBalance':0.0,
                'hasViewed':False,
                'categoryId':13,
                'status':'posted'
            },
            {
                'symbol':'',
                'isInterest':False,
                'netCost':0.0,
                'cusipNumber':'',
                'accountName':'Blue Cash Everyday - X2005',
                'description':'Autopay Payment - Thank You',
                'memo':'',
                'isCredit':True,
                'isEditable':True,
                'isCashOut':False,
                'merchantId':'zUrf4igY4ZMJgSedlLvH6b1vryI4_YkcbuRDxWVt-f8',
                'price':0.0,
                'holdingType':'',
                'lotHandling':'',
                'customReason':'',
                'userTransactionId':5176324117,
                'currency':'USD',
                'isDuplicate':False,
                'resultType':'aggregated',
                'originalDescription':'Autopay Payment - Thank You',
                'isSpending':False,
                'amount':5.0,
                'checkNumber':'',
                'transactionTypeId':1,
                'isIncome':False,
                'includeInCashManager':False,
                'merchant':'',
                'isNew':False,
                'isCashIn':True,
                'transactionDate':'2018-08-05',
                'transactionType':'Credit',
                'accountId':'10003703_12495704_48433256',
                'originalAmount':5.0,
                'isCost':False,
                'userAccountId':48433256,
                'simpleDescription':'Autopay Payment - Thank You',
                'catKeyword':'Payment Thank You',
                'runningBalance':0.0,
                'hasViewed':False,
                'categoryId':51,
                'status':'posted'
            }
        ]}
    }

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
        bal_id = db.execute("SELECT bal_id FROM balances WHERE time=:time", \
                             time=i['lastRefreshed'])
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