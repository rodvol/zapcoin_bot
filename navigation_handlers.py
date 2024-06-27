from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from staking_handlers import handle_stake
from dca_handlers import handle_dca
from presale_handlers import handle_presale
from wallet_handlers import handle_wallet
from settings_handlers import handle_settings
import logging
from database import user_has_wallet, get_user_wallet, get_all_settings, save_setting
from config import WEB3_PROVIDER_URI, SWAP_CONTRACT_ADDRESS, TELEGRAM_TOKEN, ROUTER_CONTRACT_ADDRESS
from wallet_management import create_wallet
from web3 import Web3
from config import WEB3_PROVIDER_URI
from database import get_user_address, get_user_private_key
from datetime import datetime
from liquidity_sniping import start_liquidity_sniping_task
import json

logging.basicConfig(level=logging.INFO)

web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
WETH_ADDRESS = '0x40375c92d9faf44d2f9db9bd9ba41a3317a2404f'

with open('swap_contract_abi.json') as f:
    swap_contract_abi = json.load(f)

with open('router_contract_abi.json') as f:
    router_contract_abi = json.load(f)

with open('token_contract_abi.json') as f:
    token_contract_abi = json.load(f)

swap_contract_address = SWAP_CONTRACT_ADDRESS
router_contract_address = ROUTER_CONTRACT_ADDRESS
swap_contract = web3.eth.contract(address=swap_contract_address, abi=swap_contract_abi)
router_contract = web3.eth.contract(address=router_contract_address, abi=router_contract_abi)

async def handle_start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    wallet = None
    userhaswallet = user_has_wallet(user_id)
    if userhaswallet:
        wallet = get_user_wallet(user_id)
    else:
        wallet = create_wallet(user_id)
    
    # Create the keyboard with all buttons
    keyboard = [
        [InlineKeyboardButton("Buy", callback_data='snipe'), InlineKeyboardButton("Sell & Manage", callback_data='sell_manage')],
        [InlineKeyboardButton("Staking", callback_data='staking'), InlineKeyboardButton("DCA", callback_data='dca'), InlineKeyboardButton("Presale Sniping", callback_data='presale')],
        [InlineKeyboardButton("Help", callback_data='help'), InlineKeyboardButton("Wallet", callback_data='wallet'), InlineKeyboardButton("Settings", callback_data='settings')],
        [InlineKeyboardButton("Airdrop", callback_data='airdrop'), InlineKeyboardButton("Pin", callback_data='pin'), InlineKeyboardButton("Refresh", callback_data='refresh')]
    ]

    # Check if the user already has a wallet
    if userhaswallet:
        # User has a wallet, include Refresh button and token input instructions
        text = (
            f"Welcome to Zapcoin Sniping Bot!\n"
            f"CORE Chain’s Leading Sniping Bot to trade any token, built with love for the Coretoshis!\n\n"
            f"Wallet {wallet['address'][-4:]}:\n"
            f"Address: {wallet['address']}\n"
            f"Balance: {wallet['balance']} CORE\n\n"
            "📃 Paste the Contract Address of the token you’d like to snipe."
        )
    else:
        # User does not have a wallet, display wallet creation details
        text = (
            "Welcome to Zapcoin Sniping Bot!\n"
            "CORE Chain’s Leading Sniping Bot to trade any token, built with love for the Coretoshis!\n\n"
            "You need to deposit CORE to your wallet. To start trading, deposit CORE to your Zapcoin Sniping Bot Wallet Address:\n\n"
            f"{wallet['address']} (tap to Copy)\n\n"
            "⚠️ Please Copy the Private Key and Passphrase to keep it in a safe place. Without the private key and passphrase you won’t be able to access your assets once lost. "
            "Additionally, please keep them private and never share them with anyone. We won’t be responsible if you lose your private key and passphrase.\n\n"
            f"Private Key: {wallet['private_key']} (tap to copy)\n"
            "Passphrase: <Key> (tap to copy)\n\n"
            "When you’ve deposited the asset, please make sure to tap on refresh."
        )
    context.user_data.clear()
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text=text, reply_markup=reply_markup)
    else:
        query = update.callback_query
        await query.edit_message_text(text=text, reply_markup=reply_markup)

async def handle_token_input(update: Update, context: CallbackContext):
    if not context.user_data.get('expecting_setting_value'):
        token_address = update.message.text
        context.user_data['token_address'] = token_address
        token_info = await get_token_info(token_address)  # This should fetch token details

        # Escape special characters for MarkdownV2
        def escape_markdown_v2(text):
            escape_chars = r'\*_`\[\]()~>#+-=|{}.!'
            return ''.join(['\\' + char if char in escape_chars else char for char in text])

        token_name = escape_markdown_v2(token_info['name'])
        token_detail_message = (
            f"{token_name}\n"
            f"Profit: {token_info['profit']}% / {token_info['profit_core']} CORE\n"
            f"Value: ${token_info['value_usd']} / {token_info['value_core']} CORE\n"
            f"Mcap: ${token_info['market_cap']} @ ${token_info['price']}\n"
            f"5m: {token_info['5m']}, 1h: {token_info['1h']}, 6h: {token_info['6h']}, 24h: {token_info['24h']}"
        )
        
        keyboard = [
            [InlineKeyboardButton("View Details", callback_data=f'token_detail_{token_address}')],
            [InlineKeyboardButton("Back", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(token_detail_message, reply_markup=reply_markup)
        context.user_data['expecting_token_address'] = False

async def handle_token_detail(update: Update, context: CallbackContext):
    query = update.callback_query
    token_address = context.user_data.get('token_address')
    token_info = await get_token_info(token_address)

    user_id = update.effective_user.id
    settings = get_all_settings(user_id)

    buy_left_value = settings.get('buy_left', '1.0')
    buy_right_value = settings.get('buy_right', '5.0')
    sell_left_value = settings.get('sell_left', '25')
    sell_right_value = settings.get('sell_right', '100')

    token_trade_message = (
        f"${token_info['symbol']} | {token_info['name']} |\n"
        f"{token_info['address']}\n"
        f"Profit: {token_info['profit']}% / {token_info['profit_core']} CORE\n"
        f"Value: ${token_info['value_usd']} / {token_info['value_core']} CORE\n"
        f"Mcap: ${token_info['market_cap']} @ ${token_info['price']}\n"
        f"5m: {token_info['5m']}, 1h: {token_info['1h']}, 6h: {token_info['6h']}, 24h: {token_info['24h']}\n"
        f"Net Profit: {token_info['net_profit']}% / {token_info['net_profit_core']} CORE\n"
        f"Initial: {token_info['initial_core']} CORE\n"
        f"Balance: {token_info['balance']} {token_info['symbol']}\n"
        f"Wallet Balance: {token_info['wallet_balance']} CORE\n\n"
        "⚠️ You have under 0.005 CORE in your account. Please add more to pay the Core blockchain fee."
    )

    keyboard = [
        [InlineKeyboardButton("Home", callback_data='back_to_start'), InlineKeyboardButton("Close", callback_data='close')],
        [InlineKeyboardButton(f"Buy {buy_left_value} CORE", callback_data=f'buy_{token_address}_left'), InlineKeyboardButton(f"Buy {buy_right_value} CORE", callback_data=f'buy_{token_address}_right'), InlineKeyboardButton("Buy X CORE", callback_data=f'buy_{token_address}_x')],
        [InlineKeyboardButton(f"Sell {sell_left_value}%", callback_data=f'sell_{token_address}_left'), InlineKeyboardButton(f"Sell {sell_right_value}%", callback_data=f'sell_{token_address}_right'), InlineKeyboardButton("Sell X%", callback_data=f'sell_{token_address}_x')],
        [InlineKeyboardButton("Limit Buy", callback_data=f'limit_buy_{token_address}'), InlineKeyboardButton("Limit Sell", callback_data=f'limit_sell_{token_address}')],
        [InlineKeyboardButton("Explorer", callback_data=f'explorer_{token_address}'), InlineKeyboardButton("Birdeye", callback_data=f'birdeye_{token_address}'), InlineKeyboardButton("Scan", callback_data=f'scan_{token_address}')],
        [InlineKeyboardButton("Refresh", callback_data=f'refresh_{token_address}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(token_trade_message, reply_markup=reply_markup)


async def handle_trade_action(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split('_')
    action = data[0]
    if action == 'snipe':
        await query.message.reply_text("Please enter the Contract Address you’d like to Snipe:")
        context.user_data['expecting_contract_address'] = True
        return
    token_address = data[1]
    data = query.data.split('_')
    amount = data[2] if len(data) > 2 else None
    if action == 'buy':
        if amount == 'x':
            context.user_data['buy_x'] = token_address
            await query.edit_message_text("Enter the amount of CORE you’re willing to buy with:", reply_markup=back_markup('token_detail'))
            context.user_data['expecting_token_amount'] = True  # Set the context for expecting token amount input
        else:
            await process_buy(update, context, amount)

    elif action == 'sell':
        if amount == 'x':
            context.user_data['sell_x'] = token_address
            await query.edit_message_text("Enter the % of tokens you’re willing to sell:", reply_markup=back_markup('token_detail'))
            context.user_data['expecting_token_amount'] = True  # Set the context for expecting token amount input
        else:
            await process_sell(update, context, amount)

    elif action == 'refresh':
        await handle_token_detail(update, context)

    elif action == 'explorer':
        await query.edit_message_text(f"Explorer link for {token_address}", reply_markup=back_markup('token_detail'))

    elif action == 'birdeye':
        await query.edit_message_text(f"Birdeye link for {token_address}", reply_markup=back_markup('token_detail'))

    elif action == 'scan':
        await query.edit_message_text(f"Scan link for {token_address}", reply_markup=back_markup('token_detail'))

async def handle_back(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    main_menu_keyboard = [
        [InlineKeyboardButton("Buy", callback_data='buy'), InlineKeyboardButton("Sell & Manage", callback_data='sell_manage')],
        [InlineKeyboardButton("Staking", callback_data='staking'), InlineKeyboardButton("DCA", callback_data='dca'), InlineKeyboardButton("Presale Sniping", callback_data='presale')],
        [InlineKeyboardButton("Help", callback_data='help'), InlineKeyboardButton("Wallet", callback_data='wallet'), InlineKeyboardButton("Settings", callback_data='settings')],
        [InlineKeyboardButton("Airdrop", callback_data='airdrop'), InlineKeyboardButton("Pin", callback_data='pin'), InlineKeyboardButton("Refresh", callback_data='refresh')]
    ]

    reply_markup = InlineKeyboardMarkup(main_menu_keyboard)

    # Determine which menu to return to
    if query.data == 'back_to_start':
        user_id = update.effective_user.id
        wallet = None
        userhaswallet = user_has_wallet(user_id)
        if userhaswallet:
            wallet = get_user_wallet(user_id)
        else:
            wallet = create_wallet(user_id)
        if userhaswallet:
            # User has a wallet, include Refresh button and token input instructions
            text = (
                f"Welcome to Zapcoin Sniping Bot!\n"
                f"CORE Chain’s Leading Sniping Bot to trade any token, built with love for the Coretoshis!\n\n"
                f"Wallet {wallet['address'][-4:]}:\n"
                f"Address: {wallet['address']}\n"
                f"Balance: {wallet['balance']} CORE\n\n"
                "📃 Paste the Contract Address of the token you’d like to snipe."
            )
        else:
            # User does not have a wallet, display wallet creation details
            text = (
                "Welcome to Zapcoin Sniping Bot!\n"
                "CORE Chain’s Leading Sniping Bot to trade any token, built with love for the Coretoshis!\n\n"
                "You need to deposit CORE to your wallet. To start trading, deposit CORE to your Zapcoin Sniping Bot Wallet Address:\n\n"
                f"{wallet['address']} (tap to Copy)\n\n"
                "⚠️ Please Copy the Private Key and Passphrase to keep it in a safe place. Without the private key and passphrase you won’t be able to access your assets once lost. "
                "Additionally, please keep them private and never share them with anyone. We won’t be responsible if you lose your private key and passphrase.\n\n"
                f"Private Key: {wallet['private_key']} (tap to copy)\n"
                "Passphrase: <Key> (tap to copy)\n\n"
                "When you’ve deposited the asset, please make sure to tap on refresh."
            )
        query = update.callback_query
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    elif query.data == 'back_to_stake':
        await handle_stake(update, context)
    elif query.data == 'back_to_dca':
        await handle_dca(update, context)
    elif query.data == 'back_to_presale':
        await handle_presale(update, context)
    elif query.data == 'back_to_wallet':
        await handle_wallet(update, context)
    elif query.data == 'back_to_settings':
        await handle_settings(update, context)
    elif query.data == 'back_to_help':
        await handle_help(update, context)

async def handle_help(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Back", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("If you’re seeking assistance, please join the Zapcoin Telegram Group and raise your question. An admin will try to help you when they’re online. Moreover, you can go through our White Paper for any technical help.", reply_markup=reply_markup)

async def handle_sell_manage(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Sell 25%", callback_data='sell_25')],
        [InlineKeyboardButton("Sell 50%", callback_data='sell_50')],
        [InlineKeyboardButton("Sell 100%", callback_data='sell_100')],
        [InlineKeyboardButton("Back", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Positions Overview:\n\nNo active positions.", reply_markup=reply_markup)

async def handle_pin(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Pin functionality coming soon.", reply_markup=back_markup('back_to_start'))

async def handle_refresh(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Your data has been refreshed.", reply_markup=back_markup('back_to_start'))

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])

async def handle_trade_token(update: Update, context: CallbackContext):
    query = update.callback_query
    token_info = context.user_data.get('token_info')
    if token_info:
        keyboard = [
            [InlineKeyboardButton("Buy 1 CORE", callback_data='buy_1_core'), InlineKeyboardButton("Buy 5 CORE", callback_data='buy_5_core'), InlineKeyboardButton("Buy X CORE", callback_data='buy_x_core')],
            [InlineKeyboardButton("Sell 25%", callback_data='sell_25'), InlineKeyboardButton("Sell 100%", callback_data='sell_100'), InlineKeyboardButton("Sell X%", callback_data='sell_x')],
            [InlineKeyboardButton("Explorer", callback_data='explorer'), InlineKeyboardButton("Birdeye", callback_data='birdeye'), InlineKeyboardButton("Scan", callback_data='scan')],
            [InlineKeyboardButton("Refresh", callback_data='refresh_token'), InlineKeyboardButton("Home", callback_data='back_to_start'), InlineKeyboardButton("Close", callback_data='close')]
        ]
        await query.edit_message_text(
            text=(
                f"${token_info['ticker']} - {token_info['name']}\n"
                f"{token_info['address']} (tap to copy)\n\n"
                f"Profit: {token_info['profit']}%\n"
                f"Value: {token_info['value']} CORE\n"
                f"Market Cap: ${token_info['market_cap']}\n"
                f"Price: ${token_info['price']}\n"
                f"Initial: {token_info['initial']} CORE\n"
                f"Balance: {token_info['balance']} {token_info['ticker']}\n"
                f"Wallet Balance: {token_info['wallet_balance']} CORE\n\n"
                "⚠️ You need to have a minimum of 1 CORE in your account to conduct transactions."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    await query.answer()

async def handle_buy(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    settings = get_all_settings(user_id)
    
    action = query.data.split('_')[-1]
    token_address = context.user_data.get('token_address')
    
    print(f"handle_buy {token_address} {action}")

    if action == 'left':
        amount = settings.get('buy_left', '1.0').split()[0]
        await process_buy(update, context, amount)
    elif action == 'right':
        amount = settings.get('buy_right', '5.0').split()[0]
        await process_buy(update, context, amount)
    elif action == 'x':
        context.user_data['buy_x'] = token_address
        context.user_data['expecting_token_amount'] = True
        await query.edit_message_text("Enter the amount of CORE you’re willing to buy with:", reply_markup=back_markup('token_detail'))

async def process_buy(update: Update, context: CallbackContext, amount):
    query = update.callback_query
    token_address = context.user_data.get('token_address')
    user_id = update.effective_user.id
    try:
        tx_hash = await buy_token(get_user_address(user_id), token_address, float(amount), get_user_private_key(user_id))
        await query.message.reply_text(
            text=f"Bought {amount} tokens for {amount} CORE.\nTransaction Hash: {tx_hash}",
            reply_markup=back_markup('token')
        )
    except Exception as e:
        await query.message.reply_text(
            text=f"Buying {token_address} worth {amount} CORE\nThe transaction wasn’t executed due to an error. Contact Zapcoin Support if the issue continues in their Telegram Group\nError: {str(e)}",
            reply_markup=back_markup('token')
        )

async def buy_token(wallet_address, token_address, amount, private_key):

    # sender_address = "0x39181Eb8b171e7Fef9E2cc948e2b7EF3b5A44F0e"
    # private_key = "b40dfef60bd31f75da02468bac4f4957acfdf89eeb16dc5e6fedc751c647d8d0"
    # receiver_address = "0xE307b431864820a0c7014A60BeCD3AC643eFAA01"
    # amount = web3.to_wei(2, 'ether')
    # nonce = web3.eth.get_transaction_count(sender_address)
    # gas_price = web3.eth.gas_price
    # gas_limit = 500_000
    # tx = {
    #     'nonce': nonce,
    #     'to': receiver_address,
    #     'value': amount,
    #     'gas': gas_limit,
    #     'gasPrice': gas_price,
    #     'chainId': 1116 
    # }
    # signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    # tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # return

    nonce = web3.eth.get_transaction_count(wallet_address)
    gas_price = web3.eth.gas_price
    amount = 0.01

    path = [web3.to_checksum_address(WETH_ADDRESS), web3.to_checksum_address(token_address)]
    amountIn = web3.to_wei(amount, 'ether')
    amountsOut = router_contract.functions.getAmountsOut(amountIn, path).call()
    amountOut = amountsOut[1]
    deadline = int(datetime.now().timestamp()) + 60 * 20 

    print(f"buy_token {amountOut} {path} {wallet_address} {deadline}")

    tx = router_contract.functions.swapETHForExactTokens(
        amountOut,
        path,
        wallet_address,
        deadline
    ).build_transaction({
        'from': wallet_address,
        'value': web3.to_wei(amount, 'ether'),
        'gas': 500_000,
        'gasPrice': gas_price,
        'nonce': nonce,
        'chainId': 1116
    })

    try:
        estimated_gas = web3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas
    except Exception as e:
        raise Exception(f"Estimated Gas: {str(e)}")

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise Exception(f"Transaction failed with status {receipt.status}")

        after_balance = web3.eth.get_balance(wallet_address)
        return tx_hash.hex(), after_balance
    except Exception as e:
        raise Exception(f"Transaction failed: {str(e)}")

async def handle_sell(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    settings = get_all_settings(user_id)
    
    action = query.data.split('_')[-1]
    token_address = context.user_data.get('token_address')
    
    if action == 'left':
        percentage = settings.get('sell_left', '25').split()[0]
        await process_sell(update, context, percentage)
    elif action == 'right':
        percentage = settings.get('sell_right', '100').split()[0]
        await process_sell(update, context, percentage)
    elif action == 'x':
        context.user_data['sell_x'] = token_address
        context.user_data['expecting_token_amount'] = True
        await query.edit_message_text("Enter the % of tokens you’re willing to sell:", reply_markup=back_markup('token_detail'))

async def process_sell(update: Update, context: CallbackContext, percentage):
    query = update.callback_query
    token_address = context.user_data.get('token_address')
    user_id = update.effective_user.id
    try:
        tx_hash = await sell_token(get_user_address(user_id), token_address, float(percentage), get_user_private_key(user_id))
        await query.message.reply_text(
            text=f"Sold {percentage}% tokens for {token_address}.\nTransaction Hash: {tx_hash}",
            reply_markup=back_markup('token')
        )
    except Exception as e:
        await query.message.reply_text(
            text=f"Selling {token_address} worth {percentage}%\nThe transaction wasn’t executed due to an error. Contact Zapcoin Support if the issue continues in their Telegram Group\nError: {str(e)}",
            reply_markup=back_markup('token')
        )

async def sell_token(wallet_address, token_address, percentage, private_key):
    print(f"sell_token {wallet_address} {token_address} {percentage} {private_key}")
    try:
        token_contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=token_contract_abi)
        token_balance = token_contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
        amount_to_sell = int(token_balance * (percentage / 100))
        try:
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            decimals = 9
        print(decimals)
        amount_to_sell = int( amount_to_sell / (10 ** decimals))
        print(amount_to_sell)
        if amount_to_sell == 0:
            raise Exception("The amount to sell is zero. Please check the token balance and percentage.")

        nonce = web3.eth.get_transaction_count(Web3.to_checksum_address(wallet_address))
        gas_price = web3.eth.gas_price

        approve_tx = token_contract.functions.approve(Web3.to_checksum_address(ROUTER_CONTRACT_ADDRESS), amount_to_sell).build_transaction({
            'from': Web3.to_checksum_address(wallet_address),
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': gas_price,
            'chainId': 1116
        })

        signed_approve_tx = web3.eth.account.sign_transaction(approve_tx, private_key)

        try:
            approve_tx_hash = web3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
            approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash)

            if approve_receipt.status != 1:
                raise Exception(f"Approval transaction failed with status {approve_receipt.status}")

            router_contract = web3.eth.contract(address=Web3.to_checksum_address(ROUTER_CONTRACT_ADDRESS), abi=router_contract_abi)
            path = [Web3.to_checksum_address(token_address), Web3.to_checksum_address(WETH_ADDRESS)]
            deadline = int(datetime.now().timestamp()) + 60 * 20 
            nonce += 1
            print(f"swapExactTokensForETH {amount_to_sell} {path} {wallet_address}")
            swap_tx = router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                amount_to_sell,
                0, 
                path,
                Web3.to_checksum_address(wallet_address),
                deadline
            ).build_transaction({
                'from': Web3.to_checksum_address(wallet_address),
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': 1116
            })

            estimated_gas = web3.eth.estimate_gas(swap_tx)
            swap_tx['gas'] = estimated_gas

            signed_swap_tx = web3.eth.account.sign_transaction(swap_tx, private_key)
            swap_tx_hash = web3.eth.send_raw_transaction(signed_swap_tx.rawTransaction)
            swap_receipt = web3.eth.wait_for_transaction_receipt(swap_tx_hash)

            if swap_receipt.status != 1:
                raise Exception(f"Swap transaction failed with status {swap_receipt.status}")

            return swap_tx_hash.hex()
        except Exception as e:
            raise Exception(f"Transaction failed: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


async def get_token_info(token_address):
    # Dummy implementation, replace with actual logic to fetch token details
    return {
        'name': 'Baby LandWolf',
        'symbol': 'BLW',
        'address': token_address,
        'profit': 97.94,
        'profit_core': -0.0334,
        'value_usd': 0.09,
        'value_core': 0.0007,
        'market_cap': 721.74,
        'price': 0.0722,
        '5m': '+0.17%',
        '1h': '-16.73%',
        '6h': '-4.68%',
        '24h': '-77.32%',
        'net_profit': -97.96,
        'net_profit_core': -0.0334,
        'initial_core': 0.0341,
        'balance': '1.28M',
        'wallet_balance': 0.0
    }

def get_wallet_balance(address):
    # Logic to get the wallet balance
    pass

async def handle_refresh(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_wallet = get_user_wallet(user_id)
    balance = get_wallet_balance(user_wallet['address'])

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=(
            f"Zapcoin Sniping Bot\n"
            f"Wallet {user_wallet['address'][-4:]}\n"
            f"Address: {user_wallet['address']}\n"
            f"Balance: {balance} CORE\n\n"
            "📃 Paste the Contract Address of the token you’d like to snipe"
        ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Refresh", callback_data='refresh')]])
    )
    context.user_data['awaiting_token'] = True

async def handle_limit_buy(update: Update, context: CallbackContext):
    query = update.callback_query
    token_address = query.data.split('_')[2]
    context.user_data['limit_token_address'] = token_address
    await query.edit_message_text(f"At what price would you like to buy {token_address}?", reply_markup=back_markup('token_detail'))
    context.user_data['expecting_limit_price'] = 'buy'

async def handle_limit_sell(update: Update, context: CallbackContext):
    query = update.callback_query
    token_address = query.data.split('_')[2]
    context.user_data['limit_token_address'] = token_address
    await query.edit_message_text(f"At what price would you like to sell {token_address}?", reply_markup=back_markup('token_detail'))
    context.user_data['expecting_limit_price'] = 'sell'

async def execute_limit_buy(token_address, limit_price, amount, context):
    context.user_data['limit_buy_order'] = {
        'token_address': token_address,
        'limit_price': limit_price,
        'amount': amount
    }
    await context.bot.send_message(chat_id=context.user_data['chat_id'], text=f"Limit buy order placed: Buy {amount} CORE worth of {token_address} at {limit_price}.")

async def execute_limit_sell(token_address, limit_price, amount, context):
    context.user_data['limit_sell_order'] = {
        'token_address': token_address,
        'limit_price': limit_price,
        'amount': amount
    }
    await context.bot.send_message(chat_id=context.user_data['chat_id'], text=f"Limit sell order placed: Sell {amount} {token_address} at {limit_price}.")

async def handle_snipe(update: Update, context: CallbackContext):
    await update.message.reply_text("Please enter the Contract Address you’d like to Snipe.")
    context.user_data['awaiting_contract_address'] = True

async def snipe_token(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    contract_address = context.user_data['contract_address']
    core_amount = context.user_data['core_amount']
    address = get_user_address(user_id)
    private_key = get_user_private_key(user_id)

    sniping_info = {
        'token_address': contract_address,
        'amount': core_amount,
        'address': address,
        'private_key': private_key
    }

    await start_liquidity_sniping_task(user_id, sniping_info)

    await update.message.reply_text(f"Buying {contract_address} worth {core_amount} CORE")
    await update.message.reply_text("Sniping task started. You will be notified once the transaction is complete.")