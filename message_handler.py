from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from wallet_handlers import import_wallet, get_balance, get_transaction_history, get_user_address, get_user_private_key
from liquidity_sniping_handlers import start_liquidity_sniping_task
from dca_handlers import start_dca_task
from presale_handlers import participate_in_presale
import logging
logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: CallbackContext):
    core_decimal_places = 18
    user_id = update.effective_user.id

    if context.user_data.get('import_wallet'):
        private_key = update.message.text
        import_data = context.user_data['import_wallet']
        address = import_wallet(import_data['user_id'], private_key)
        await update.message.reply_text(f'Wallet imported!\nAddress: {address}', reply_markup=back_markup('wallet'))
        context.user_data.pop('import_wallet')

    elif context.user_data.get('check_balance'):
        address = update.message.text
        try:
            balance = get_balance(address, web3)
            await update.message.reply_text(f'Balance: {balance / (10 ** core_decimal_places)} CORE', reply_markup=back_markup('wallet'))
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}', reply_markup=back_markup('wallet'))
        context.user_data['check_balance'] = False

    elif context.user_data.get('check_history'):
        address = update.message.text
        try:
            history = get_transaction_history(address, web3)
            history_str = "\n".join([f"{tx['hash']}: {int(tx['value']) / (10 ** core_decimal_places)} CORE" for tx in history])
            await update.message.reply_text(f'Transaction History:\n{history_str}', reply_markup=back_markup('wallet'))
        except Exception as e:
            await update.message.reply_text(f'Error: {str(e)}', reply_markup=back_markup('wallet'))
        context.user_data['check_history'] = False

    elif context.user_data.get('liquidity_sniping_token_address'):
        context.user_data['liquidity_sniping'] = {'token_address': update.message.text}
        await update.message.reply_text("Please enter the amount of CORE you want to spend for liquidity sniping:", reply_markup=back_markup('liquidity_sniping'))
        context.user_data.pop('liquidity_sniping_token_address')
        context.user_data['liquidity_sniping_amount'] = True

    elif context.user_data.get('liquidity_sniping_amount'):
        amount = float(update.message.text)
        sniping_info = context.user_data['liquidity_sniping']
        sniping_info['amount'] = amount
        sniping_info['address'] = get_user_address(user_id)
        sniping_info['private_key'] = get_user_private_key(user_id)
        await update.message.reply_text("Starting liquidity sniping...", reply_markup=back_markup('liquidity_sniping'))
        await start_liquidity_sniping_task(user_id, sniping_info)
        context.user_data.pop('liquidity_sniping_amount')

    elif context.user_data.get('staking_amount'):
        amount = float(update.message.text)
        context.user_data['staking'] = {'amount': amount}
        await update.message.reply_text("We only support Everstake Validator at the moment. Are you okay with it? If Yes please proceed and tap on 'Continue'.\nFor more details about Everstake and APY-related information, check it out: https://stake.coredao.org/validator/0x307f36ff0aff7000ebd4eea1e8e9bbbfa0e1134c", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Continue", callback_data='confirm_stake')], [InlineKeyboardButton("Back", callback_data='back_to_stake')]]))
        context.user_data.pop('staking_amount')

    elif context.user_data.get('dca_ca'):
        context.user_data['dca'] = {'ca': update.message.text}
        await update.message.reply_text("Input the Amount of CORE you’d like to snipe with:", reply_markup=back_markup('dca'))
        context.user_data.pop('dca_ca')
        context.user_data['dca_amount'] = True

    elif context.user_data.get('dca_amount'):
        amount = float(update.message.text)
        context.user_data['dca']['amount'] = amount
        await update.message.reply_text("Input how frequently (In days) you’d like to DCA:", reply_markup=back_markup('dca'))
        context.user_data.pop('dca_amount')
        context.user_data['dca_frequency'] = True

    elif context.user_data.get('dca_frequency'):
        frequency = int(update.message.text)
        dca_info = context.user_data['dca']
        dca_info['frequency'] = frequency
        await update.message.reply_text(f"Started DCA’ing. The first DCA transaction will happen in {frequency} days.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel DCA’ing", callback_data='cancel_dca')], [InlineKeyboardButton("Back", callback_data='back_to_dca')]]))
        await start_dca_task(user_id, dca_info)
        context.user_data.pop('dca_frequency')

    elif context.user_data.get('presale_link'):
        context.user_data['presale'] = {'link': update.message.text}
        await update.message.reply_text("How many CORE would you like to contribute?", reply_markup=back_markup('presale'))
        context.user_data.pop('presale_link')
        context.user_data['presale_amount'] = True

    elif context.user_data.get('presale_amount'):
        amount = float(update.message.text)
        presale_info = context.user_data['presale']
        presale_info['amount'] = amount
        await update.message.reply_text(f"Buying {amount} CORE for presale.", reply_markup=back_markup('presale'))
        await participate_in_presale(user_id, presale_info)
        context.user_data.pop('presale_amount')

    elif context.user_data.get('slippage'):
        slippage = int(update.message.text)
        context.user_data['slippage'] = slippage
        await update.message.reply_text(f"Slippage changed to {slippage}%.", reply_markup=back_markup('settings'))
        context.user_data.pop('slippage')

    elif context.user_data.get('min_position_value'):
        min_value = float(update.message.text)
        context.user_data['min_position_value'] = min_value
        await update.message.reply_text(f"Minimum position value set to {min_value} CORE.", reply_markup=back_markup('settings'))
        context.user_data.pop('min_position_value')

    elif context.user_data.get('max_buy_tax'):
        max_tax = float(update.message.text)
        context.user_data['max_buy_tax'] = max_tax
        await update.message.reply_text(f"Maximum buy tax set to {max_tax}%.", reply_markup=back_markup('settings'))
        context.user_data.pop('max_buy_tax')

    elif context.user_data.get('max_sell_tax'):
        max_tax = float(update.message.text)
        context.user_data['max_sell_tax'] = max_tax
        await update.message.reply_text(f"Maximum sell tax set to {max_tax}%.", reply_markup=back_markup('settings'))
        context.user_data.pop('max_sell_tax')

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])
