from pymongo import MongoClient
from config import MONGODB_URI
from bson.objectid import ObjectId

client = MongoClient(MONGODB_URI)
db = client['telegram_zapcoin_bot']

DEFAULT_SETTINGS = {
    'transaction_priority': 'medium',
    'buy_left': '1.0',
    'buy_right': '5.0',
    'sell_left': '25',
    'sell_right': '100',
    'slippage_buy': '10',
    'slippage_sell': '15',
    'max_price_impact': '15',
    'max_buy_tax': '25',
    'max_sell_tax': '25',
    'min_position_value': '1',
}

def insert_wallet(user_id, address, private_key):
    wallet = {
        'user_id': user_id,
        'address': address,
        'private_key': private_key,
        'balance': 0.0,
        'enabled': True
    }
    db.wallets.insert_one(wallet)

def get_wallet(user_id, address):
    return db.wallets.find_one({'user_id': user_id, 'address': address})

def update_wallet_balance(user_id, address, balance):
    db.wallets.update_one({'user_id': user_id, 'address': address}, {'$set': {'balance': balance}})

def get_all_wallets(user_id):
    return list(db.wallets.find({'user_id': user_id}))

def toggle_wallet_enabled(user_id, wallet_id):
    wallet = db.wallets.find_one({'_id': ObjectId(wallet_id), 'user_id': user_id})
    if wallet:
        new_status = not wallet['enabled']
        db.wallets.update_one({'_id': ObjectId(wallet_id), 'user_id': user_id}, {'$set': {'enabled': new_status}})

def get_spending_limits(user_id, limit_type):
    return db.limits.find_one({'user_id': user_id, 'type': limit_type})

def set_spending_limits(user_id, limit_type, limit):
    db.limits.update_one(
        {'user_id': user_id, 'type': limit_type},
        {'$set': {'limit': limit}},
        upsert=True
    )

def get_active_wallets(user_id):
    return list(db.wallets.find({'enabled': True, 'user_id': user_id}))

def get_user_address(user_id):
    wallet = db.wallets.find_one({'user_id': user_id, 'enabled': True})
    if wallet:
        return wallet['address']
    return None

def get_user_private_key(user_id):
    wallet = db.wallets.find_one({'user_id': user_id, 'enabled': True})
    if wallet:
        return wallet['private_key']
    return None

def user_has_wallet(user_id):
    count = db.wallets.count_documents({'user_id': user_id})
    return count > 0

def get_user_wallet(user_id):
    result = list(db.wallets.find({'user_id': user_id}))
    if len(result) > 0:
        return result[0]
    else:
        return None
    
def save_setting(user_id, setting_key, setting_value):
    db.settings.update_one(
        {'user_id': user_id},
        {'$set': {setting_key: setting_value}},
        upsert=True
    )

def get_setting(user_id, setting_key, default_value=None):
    setting = db.settings.find_one({'user_id': user_id})
    if setting and setting_key in setting:
        return setting[setting_key]
    return default_value

def initialize_settings(user_id):
    user_settings = db.settings.find_one({'user_id': user_id})
    if not user_settings:
        for key, value in DEFAULT_SETTINGS.items():
            save_setting(user_id, key, value)

def get_all_settings(user_id):
    settings = db.settings.find_one({'user_id': user_id})
    if not settings:
        initialize_settings(user_id)
        settings = db.settings.find_one({'user_id': user_id})
    return settings
