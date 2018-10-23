# MIT licensed API for accessing account/transaction data via Personal Capital
# User must have Personal Capital account for this app to work.
# https://github.com/haochi/personalcapital
from personalcapital import PersonalCapital, RequireTwoFactorException, TwoFactorVerificationModeEnum
import getpass

pc = PersonalCapital()

email = input('Email: ')
password = getpass.getpass('Password: ')

try:
    pc.login(email, password)
except RequireTwoFactorException:
    pc.two_factor_challenge(TwoFactorVerificationModeEnum.SMS)
    pc.two_factor_authenticate(TwoFactorVerificationModeEnum.SMS, input('SMS Authentication Code: '))
    pc.authenticate_password(password)

accounts_response = pc.fetch('/newaccount/getAccounts')
accounts = accounts_response.json()['spData']

for i in accounts["accounts"]:
    print(f'Accounts: {i["originalName"]}')