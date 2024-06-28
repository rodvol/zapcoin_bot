import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from web3 import Web3
from eth_account import Account
from database import insert_wallet, get_wallet, update_wallet_balance, get_all_wallets, toggle_wallet_enabled, get_user_address, get_user_private_key, get_user_wallet, get_user_address, get_all_wallets, set_active_wallet
from config import CORE_SCAN_TOKEN, WEB3_PROVIDER_URI
import requests
from wallet_management import create_wallet
import logging
logging.basicConfig(level=logging.INFO)

web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))

def import_wallet(user_id, private_key):
    account = Account.from_key(private_key)
    insert_wallet(user_id, account.address, private_key)
    return account.address

def get_balance(address, web3_instance):
    url = f'https://openapi.coredao.org/api?module=account&action=balance&address={address}&apikey={CORE_SCAN_TOKEN}'
    response = requests.get(url)
    balance = response.json()['result']
    return int(balance)

def get_transaction_history(address, web3_instance):
    url = f'https://openapi.coredao.org/api?module=account&action=txlist&address={address}&startblock=0&endblock={web3_instance.eth.block_number}&page=1&offset=10&sort=desc&apikey={CORE_SCAN_TOKEN}'
    response = requests.get(url)
    transactions = response.json()['result']
    return transactions

async def handle_wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = get_user_wallet(user_id)
    balance = wallet['balance']
    address = wallet['address']

    keyboard = [
        [InlineKeyboardButton("View on Corescan", url=f"https://scan.coredao.org/address/{address}"), InlineKeyboardButton("Close", callback_data='back_to_start')],
        [InlineKeyboardButton("Deposit CORE", callback_data='deposit_core')],
        [InlineKeyboardButton("Withdraw all CORE", callback_data='withdraw_all_core'), InlineKeyboardButton("Withdraw X CORE", callback_data='withdraw_x_core')],
        [InlineKeyboardButton("Account", callback_data='switch_account')],
        [InlineKeyboardButton("Export Passphrase", callback_data='export_passphrase'), InlineKeyboardButton("Export Private Key", callback_data='export_private_key')],
        [InlineKeyboardButton("Create a New Wallet", callback_data='create_new_wallet')],
        [InlineKeyboardButton("Refresh", callback_data='refresh_wallet')]
    ]

    text = (
        f"Your Wallet:\n\n"
        f"Address: {address}\n"
        f"Balance: {balance} CORE\n\n"
        "Tap to copy the address and send CORE to deposit."
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

async def handle_deposit_core(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    wallet = get_user_wallet(user_id)
    address = wallet['address']

    # Generate QR code for the address
    img = qrcode.make(address)
    img_path = f"./qrcodes/{user_id}_qrcode.png"
    img.save(img_path)

    await query.edit_message_text(f"To Deposit CORE, send CORE to this address: {address}")
    await query.message.reply_photo(photo=open(img_path, 'rb'))

async def handle_withdraw_all_core(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text("Paste the Destination Address:")
    context.user_data['expecting_withdraw_all_address'] = True

async def handle_withdraw_x_core(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text("Paste the Destination Address:")
    context.user_data['expecting_withdraw_x_address'] = True

async def handle_export_private_key(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    private_key = get_user_private_key(user_id)
    await update.callback_query.message.reply_text(
        f"Your Wallet’s Private Key is: {private_key}. Please don’t share this with anyone as it can put your wallet at risk once shared. Store it in a safe place"
    )

async def handle_export_passphrase(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    passphrase = "example_passphrase"  # Replace with actual logic to fetch passphrase
    await update.callback_query.message.reply_text(
        f"Your Wallet’s Passphrase is: {passphrase}. Please don’t share this with anyone as it can put your wallet at risk once shared. Store it in a safe place"
    )

async def handle_create_new_wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = create_wallet(user_id)

    text = (
        "You need to deposit CORE to your wallet. To start trading, deposit CORE to your Zapcoin Sniping Bot Wallet Address:\n\n"
        f"{wallet['address']} (tap to Copy)\n\n"
        "⚠️ Please Copy the Private Key and Passphrase to keep it in a safe place. Without the private key and passphrase you won’t be able to access your assets once lost. "
        "Additionally, please keep them private and never share them with anyone. We won’t be responsible if you lose your private key and passphrase.\n\n"
        f"Private Key: {wallet['private_key']} (tap to copy)\n"
        "Passphrase: <Key> (tap to copy)\n\n"
        "When you’ve deposited the asset, please make sure to tap on refresh."
    )

    await update.callback_query.message.reply_text(text)

async def handle_refresh_wallet(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = get_user_wallet(user_id)
    balance = wallet['balance']
    address = wallet['address']

    text = (
        f"Your Wallet:\n\n"
        f"Address: {address}\n"
        f"Balance: {balance} CORE\n\n"
        "Tap to copy the address and send CORE to deposit."
    )

    keyboard = [
        [InlineKeyboardButton("View on Corescan", url=f"https://scan.coredao.org/address/{address}"), InlineKeyboardButton("Close", callback_data='back_to_start')],
        [InlineKeyboardButton("Deposit CORE", callback_data='deposit_core')],
        [InlineKeyboardButton("Withdraw all CORE", callback_data='withdraw_all_core'), InlineKeyboardButton("Withdraw X CORE", callback_data='withdraw_x_core')],
        [InlineKeyboardButton("Account", callback_data='switch_account')],
        [InlineKeyboardButton("Export Passphrase", callback_data='export_passphrase'), InlineKeyboardButton("Export Private Key", callback_data='export_private_key')],
        [InlineKeyboardButton("Create a New Wallet", callback_data='create_new_wallet')],
        [InlineKeyboardButton("Refresh", callback_data='refresh_wallet')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def handle_switch_account(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallets = get_all_wallets(user_id)  # Fetch all wallets

    keyboard = []
    for wallet in wallets:
        keyboard.append([InlineKeyboardButton(wallet['address'], callback_data=f'switch_to_{wallet["address"]}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Select the wallet to switch to:", reply_markup=reply_markup)

async def switch_to_account(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    wallet_address = query.data.split('_')[-1]
    wallets = get_all_wallets(user_id)
    new_active_wallet = next(wallet for wallet in wallets if wallet['address'] == wallet_address)
    set_active_wallet(user_id, new_active_wallet['address'])

    await query.answer("Switched active wallet.")
    await handle_wallet(update, context)
