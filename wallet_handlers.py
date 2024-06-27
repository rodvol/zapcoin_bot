from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from web3 import Web3
from eth_account import Account
from database import insert_wallet, get_wallet, update_wallet_balance, get_all_wallets, toggle_wallet_enabled, get_user_address, get_user_private_key
from config import CORE_SCAN_TOKEN, WEB3_PROVIDER_URI
import requests
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
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    # address = get_user_address(user_id)
    # balance = get_balance(address, web3) / (10 ** 18)
    address = "0x000"
    balance = 0
    keyboard = [
        [InlineKeyboardButton("View on Corescan", callback_data='view_on_solscan')],
        [InlineKeyboardButton("Close", callback_data='back_to_start')],
        [InlineKeyboardButton("Deposit CORE", callback_data='deposit_sol')],
        [InlineKeyboardButton("Withdraw all CORE", callback_data='withdraw_all_sol'), InlineKeyboardButton("Withdraw X CORE", callback_data='withdraw_x_sol')],
        [InlineKeyboardButton("Reset Wallet", callback_data='reset_wallet'), InlineKeyboardButton("Export Private Key", callback_data='export_private_key')],
        [InlineKeyboardButton("Refresh", callback_data='refresh_wallet')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Your Wallet:\n\nAddress: {address}\nBalance: {balance:.6f} CORE\n\nTap to copy the address and send SOL to deposit.", reply_markup=reply_markup)

async def handle_create_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    account = Account.create()
    insert_wallet(user_id, account.address, account._private_key.hex())
    await query.edit_message_text(f'Wallet created!\nAddress: {account.address}\nPrivate Key: {account._private_key.hex()}', reply_markup=back_markup('wallet'))

async def handle_import_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Please enter the private key of the wallet you want to import:', reply_markup=back_markup('wallet'))
    context.user_data['import_wallet'] = {'user_id': update.effective_user.id}

async def handle_check_balance(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Please enter the wallet address to check balance:', reply_markup=back_markup('wallet'))
    context.user_data['check_balance'] = True

async def handle_transaction_history(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Please enter the wallet address to check transaction history:', reply_markup=back_markup('wallet'))
    context.user_data['check_history'] = True

async def handle_select_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    wallets = get_all_wallets(user_id)
    if not wallets:
        await query.edit_message_text("No wallets found. Please create or import a wallet first.", reply_markup=back_markup('wallet'))
        return

    keyboard = [[InlineKeyboardButton(wallet['address'], callback_data=f'toggle_{wallet["_id"]}') for wallet in wallets]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select a wallet to toggle its status:", reply_markup=reply_markup)

async def handle_toggle_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    wallet_id = query.data.split('_')[1]
    toggle_wallet_enabled(user_id, wallet_id)
    await query.edit_message_text("Wallet status toggled.", reply_markup=back_markup('wallet'))

async def handle_deposit_sol(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    address = get_user_address(update.effective_user.id)
    await query.edit_message_text(f"To deposit SOL, send SOL to this address: {address}\n\nTap to copy the address.", reply_markup=back_markup('wallet'))

async def handle_withdraw_all_sol(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Please enter the destination address:', reply_markup=back_markup('wallet'))
    context.user_data['withdraw_all_sol'] = True

async def handle_withdraw_x_sol(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Please enter the destination address:', reply_markup=back_markup('wallet'))
    context.user_data['withdraw_x_sol'] = True

async def handle_reset_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    wallet = get_wallet(user_id, 'enabled')
    if wallet:
        reset_wallet(user_id)
        await query.edit_message_text("Wallet reset successfully.", reply_markup=back_markup('wallet'))
    else:
        await query.edit_message_text("No enabled wallet found to reset.", reply_markup=back_markup('wallet'))

async def handle_export_private_key(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    private_key = get_user_private_key(update.effective_user.id)
    await query.edit_message_text(f"Your Wallet’s Private Key is: {private_key}\n\nPlease don’t share this with anyone as it can put your wallet at risk once shared. Store it in a safe place.", reply_markup=back_markup('wallet'))

async def handle_refresh_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    address = get_user_address(user_id)
    balance = get_balance(address, web3) / (10 ** 18)
    await query.edit_message_text(f"Your Wallet:\n\nAddress: {address}\nBalance: {balance:.6f} CORE\n\nTap to copy the address and send SOL to deposit.", reply_markup=back_markup('wallet'))

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])


