from web3 import Web3
from eth_account import Account
from database import insert_wallet, get_active_wallets as db_get_active_wallets, get_user_address as db_get_user_address, get_user_private_key as db_get_user_private_key, get_all_wallets as db_get_all_wallets, toggle_wallet_enabled as db_toggle_wallet_enabled
from config import CORE_SCAN_TOKEN, WEB3_PROVIDER_URI
import requests
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.INFO)

web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

def create_wallet(user_id):
    account = Account.create()
    insert_wallet(user_id, account.address, account._private_key.hex())
    return { 'address': account.address, 'private_key' : account._private_key.hex() }

def import_wallet(user_id, private_key):
    account = Account.from_key(private_key)
    insert_wallet(user_id, account.address, private_key)
    return account.address

def get_balance(address, web3_instance):
    url = f'https://openapi.coredao.org/api?module=account&action=balance&address={address}&apikey={CORE_SCAN_TOKEN}'
    response = requests.get(url)
    balance = response.json()['result']
    return balance

def get_transaction_history(address, web3_instance):
    url = f'https://openapi.coredao.org/api?module=account&action=txlist&address={address}&startblock=0&endblock={web3_instance.eth.block_number}&page=1&offset=10&sort=desc&apikey={CORE_SCAN_TOKEN}'
    response = requests.get(url)
    transactions = response.json()['result']
    return transactions

def time_ago_from_timestamp(timestamp_str):
    timestamp = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Z %Y')
    time_diff = datetime.utcnow() - timestamp
    if time_diff < timedelta(minutes=1):
        return f"{int(time_diff.total_seconds())} seconds ago"
    elif time_diff < timedelta(hours=1):
        return f"{int(time_diff.total_seconds() / 60)} minutes ago"
    elif time_diff < timedelta(days=1):
        return f"{int(time_diff.total_seconds() / 3600)} hours ago"
    else:
        return f"{int(time_diff.total_seconds() / 86400)} days ago"

def get_active_wallets(user_id):
    return db_get_active_wallets(user_id)

def get_user_address(user_id):
    return db_get_user_address(user_id)

def get_user_private_key(user_id):
    return db_get_user_private_key(user_id)

def toggle_wallet_enabled(user_id, wallet_id):
    return db_toggle_wallet_enabled(user_id, wallet_id)

def get_all_wallets(user_id):
    return db_get_all_wallets(user_id)
