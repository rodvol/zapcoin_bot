from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from staking_handlers import handle_stake, handle_confirm_stake, handle_claim
from dca_handlers import handle_dca,  handle_cancel_dca, handle_dca_address, handle_dca_amount, handle_dca_frequency
from presale_handlers import handle_presale, handle_presale_link, handle_presale_amount, handle_claimsale
from settings_handlers import (
    handle_settings, handle_edit_buy_buttons_left, handle_edit_buy_buttons_right, handle_edit_sell_buttons_left, handle_edit_sell_buttons_right, handle_edit_slippage_sell, handle_edit_slippage_buy,
    handle_edit_max_price_impact, handle_edit_mev_protect, handle_edit_transaction_priority,
    handle_priority_change, handle_edit_min_position_value, handle_edit_max_buy_tax,
    handle_edit_max_sell_tax, save_setting_value, 
)
from airdrop_handlers import handle_airdrop
from wallet_handlers import (handle_wallet, handle_export_private_key, handle_refresh_wallet, handle_deposit_core, handle_withdraw_all_core,
                             handle_withdraw_x_core, handle_export_passphrase, handle_create_new_wallet, handle_switch_account, switch_to_account)
from liquidity_sniping_handlers import handle_liquidity_sniping, handle_start_liquidity_sniping, handle_stop_liquidity_sniping, handle_stop_sniping_callback
from navigation_handlers import ( handle_back, handle_start, handle_buy, handle_sell_manage, handle_help, handle_pin, handle_token_input, snipe_token, handle_snipe, withdraw_core,
                                 handle_trade_token, handle_token_detail, process_sell, process_buy, handle_sell, execute_limit_buy, execute_limit_sell, handle_limit_buy, handle_limit_sell, handle_trade_action, handle_refresh_token)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import get_user_wallet, get_user_private_key, get_user_address
import logging
logging.basicConfig(level=logging.INFO)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler('start', handle_start))
    application.add_handler(CommandHandler('settings', handle_settings))
    application.add_handler(CommandHandler('airdrop', handle_airdrop))
    application.add_handler(CommandHandler('stake', handle_stake))
    application.add_handler(CommandHandler('claim', handle_claim))
    application.add_handler(CommandHandler('dca', handle_dca))
    application.add_handler(CommandHandler('presale', handle_presale))
    application.add_handler(CommandHandler('wallet', handle_wallet))
    application.add_handler(CommandHandler('snipe', handle_snipe))

    # Callback Query Handlers
    application.add_handler(CallbackQueryHandler(handle_wallet, pattern='wallet'))
    application.add_handler(CallbackQueryHandler(handle_deposit_core, pattern='deposit_core'))
    application.add_handler(CallbackQueryHandler(handle_withdraw_all_core, pattern='withdraw_all_core'))
    application.add_handler(CallbackQueryHandler(handle_withdraw_x_core, pattern='withdraw_x_core'))
    application.add_handler(CallbackQueryHandler(handle_export_private_key, pattern='export_private_key'))
    application.add_handler(CallbackQueryHandler(handle_export_passphrase, pattern='export_passphrase'))
    application.add_handler(CallbackQueryHandler(handle_create_new_wallet, pattern='create_new_wallet'))
    application.add_handler(CallbackQueryHandler(handle_refresh_wallet, pattern='refresh_wallet'))
    application.add_handler(CallbackQueryHandler(handle_refresh_token, pattern=r'refresh_token_*'))
    application.add_handler(CallbackQueryHandler(handle_export_private_key, pattern='export_private_key'))
    application.add_handler(CallbackQueryHandler(handle_liquidity_sniping, pattern='liquidity_sniping'))
    application.add_handler(CallbackQueryHandler(handle_start_liquidity_sniping, pattern='start_liquidity_sniping'))
    application.add_handler(CallbackQueryHandler(handle_stop_liquidity_sniping, pattern='stop_liquidity_sniping'))
    application.add_handler(CallbackQueryHandler(handle_stop_sniping_callback, pattern=r'stop_sniping_\d+'))
    application.add_handler(CallbackQueryHandler(handle_presale, pattern='presale'))
    application.add_handler(CallbackQueryHandler(handle_presale_link, pattern='presale_link'))
    application.add_handler(CallbackQueryHandler(handle_presale_amount, pattern='presale_amount'))
    application.add_handler(CallbackQueryHandler(handle_claimsale, pattern='claimsale'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_start'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_stake'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_dca'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_presale'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_wallet'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_settings'))
    application.add_handler(CallbackQueryHandler(handle_back, pattern='back_to_help'))
    application.add_handler(CallbackQueryHandler(handle_confirm_stake, pattern='confirm_stake'))
    application.add_handler(CallbackQueryHandler(handle_cancel_dca, pattern='cancel_dca'))

    application.add_handler(CallbackQueryHandler(handle_buy, pattern=r'buy_.*'))
    application.add_handler(CallbackQueryHandler(handle_sell, pattern=r'sell_.*'))
    application.add_handler(CallbackQueryHandler(handle_limit_buy, pattern=r'limit_buy_.*'))
    application.add_handler(CallbackQueryHandler(handle_limit_sell, pattern=r'limit_sell_.*'))

    application.add_handler(CallbackQueryHandler(handle_sell_manage, pattern='start_sell_manage'))
    application.add_handler(CallbackQueryHandler(handle_help, pattern='help'))
    application.add_handler(CallbackQueryHandler(handle_pin, pattern='pin'))

    application.add_handler(CallbackQueryHandler(handle_settings, pattern='settings'))
    application.add_handler(CallbackQueryHandler(handle_airdrop, pattern='airdrop'))
    application.add_handler(CallbackQueryHandler(handle_stake, pattern='stake'))
    application.add_handler(CallbackQueryHandler(handle_claim, pattern='claim'))
    application.add_handler(CallbackQueryHandler(handle_dca, pattern='dca'))
    application.add_handler(CallbackQueryHandler(handle_presale, pattern='presale'))

    # Specific handlers for settings
    application.add_handler(CallbackQueryHandler(handle_settings, pattern='settings'))
    application.add_handler(CallbackQueryHandler(handle_edit_buy_buttons_left, pattern='edit_buy_buttons_left'))
    application.add_handler(CallbackQueryHandler(handle_edit_buy_buttons_right, pattern='edit_buy_buttons_right'))
    application.add_handler(CallbackQueryHandler(handle_edit_sell_buttons_left, pattern='edit_sell_buttons_left'))
    application.add_handler(CallbackQueryHandler(handle_edit_sell_buttons_right, pattern='edit_sell_buttons_right'))
    application.add_handler(CallbackQueryHandler(handle_edit_slippage_buy, pattern='edit_slippage_buy'))
    application.add_handler(CallbackQueryHandler(handle_edit_slippage_sell, pattern='edit_slippage_sell'))
    application.add_handler(CallbackQueryHandler(handle_edit_max_price_impact, pattern='edit_max_price_impact'))
    application.add_handler(CallbackQueryHandler(handle_edit_mev_protect, pattern='edit_mev_protect'))
    application.add_handler(CallbackQueryHandler(handle_edit_transaction_priority, pattern='edit_transaction_priority'))
    application.add_handler(CallbackQueryHandler(handle_priority_change, pattern=r'priority_'))
    application.add_handler(CallbackQueryHandler(handle_edit_min_position_value, pattern='edit_min_position_value'))
    application.add_handler(CallbackQueryHandler(handle_edit_max_buy_tax, pattern='edit_max_buy_tax'))
    application.add_handler(CallbackQueryHandler(handle_edit_max_sell_tax, pattern='edit_max_sell_tax'))
    application.add_handler(CallbackQueryHandler(handle_switch_account, pattern='switch_account'))
    application.add_handler(CallbackQueryHandler(switch_to_account, pattern=r'switch_to_.*'))

    application.add_handler(CallbackQueryHandler(handle_trade_token, pattern='trade_token'))
    application.add_handler(CallbackQueryHandler(handle_token_detail, pattern=r'token_detail_.*'))

    application.add_handler(CallbackQueryHandler(handle_trade_action, pattern=r'snipe'))

    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_input))

    application.run_polling()

async def handle_input(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    context.user_data['chat_id'] = chat_id

    if context.user_data.get('expecting_setting_value'):
        await save_setting_value(update, context)
    elif context.user_data.get('expecting_limit_price'):
        token_address = context.user_data['limit_token_address']
        price = update.message.text
        context.user_data['limit_price'] = float(price)
        if context.user_data['expecting_limit_price'] == 'buy':
            await update.message.reply_text(f"How many CORE would you like to buy {token_address} with?", reply_markup=back_markup('token_detail'))
            context.user_data['expecting_limit_amount'] = 'buy'
        elif context.user_data['expecting_limit_price'] == 'sell':
            await update.message.reply_text(f"How many {token_address} would you like to sell?", reply_markup=back_markup('token_detail'))
            context.user_data['expecting_limit_amount'] = 'sell'
        context.user_data.pop('expecting_limit_price')
    elif context.user_data.get('expecting_limit_amount'):
        token_address = context.user_data['limit_token_address']
        amount = update.message.text
        limit_price = context.user_data['limit_price']
        if context.user_data['expecting_limit_amount'] == 'buy':
            await execute_limit_buy(token_address, limit_price, float(amount), context)
        elif context.user_data['expecting_limit_amount'] == 'sell':
            await execute_limit_sell(token_address, limit_price, float(amount), context)
        context.user_data.pop('expecting_limit_amount')
    elif context.user_data.get('expecting_contract_address'):
        token_address = update.message.text
        context.user_data['contract_address'] = token_address
        context.user_data['expecting_contract_address'] = False
        await update.message.reply_text("With how much CORE would you like to snipe?")
        context.user_data['expecting_snipe_amount'] = True
    elif context.user_data.get('expecting_snipe_amount'):
        amount = update.message.text
        context.user_data['core_amount'] = amount
        context.user_data['expecting_snipe_amount'] = False
        reset_sniping_context(context)
        await snipe_token(update, context)
    elif context.user_data.get('expecting_withdraw_all_address'):
        destination_address = update.message.text
        user_id = update.effective_user.id
        wallet = get_user_wallet(user_id)
        amount = wallet['balance'] 
        tx_hash = await withdraw_core(wallet['address'], destination_address, amount, get_user_private_key(user_id))
        await update.message.reply_text(f"Sent {amount} CORE\nTransaction Hash: {tx_hash}")
        context.user_data.pop('expecting_withdraw_all_address')
    elif context.user_data.get('expecting_withdraw_x_address'):
        destination_address = update.message.text
        context.user_data['withdraw_destination_address'] = destination_address
        context.user_data['expecting_withdraw_x_address'] = False
        await update.message.reply_text("Enter the Amount of CORE you’d like to send")
        context.user_data['expecting_withdraw_x_amount'] = True
    elif context.user_data.get('expecting_withdraw_x_amount'):
        amount = update.message.text
        destination_address = context.user_data['withdraw_destination_address']
        user_id = update.effective_user.id
        tx_hash = await withdraw_core(get_user_address(user_id), destination_address, amount, get_user_private_key(user_id))
        await update.message.reply_text(f"Sent {amount} CORE\nTransaction Hash: {tx_hash}")
        context.user_data.pop('expecting_withdraw_x_amount')
    elif context.user_data.get('expecting_dca_address'):
        await handle_dca_address(update, context)
    elif context.user_data.get('expecting_dca_amount'):
        await handle_dca_amount(update, context)
    elif context.user_data.get('expecting_dca_frequency'):
        await handle_dca_frequency(update, context)
    elif context.user_data.get('expecting_token_amount'):
        amount = update.message.text
        token_address = context.user_data.pop('buy_x', None)
        if token_address:
            context.user_data['expecting_token_amount'] = False
            await process_buy(update, context, amount)
        else:
            token_address = context.user_data.pop('sell_x', None)
            if token_address:
                context.user_data['expecting_token_amount'] = False
                await process_sell(update, context, amount)
    else:
        await handle_token_input(update, context)

async def handle_token_amount_input(update: Update, context: CallbackContext):
    if 'buy_x' in context.user_data:
        amount = update.message.text
        token_address = context.user_data.pop('buy_x')
        await update.message.reply_text(f"Buying {token_address} worth {amount} CORE")
        await process_buy(update, context, amount)
        context.user_data['expecting_token_amount'] = False
    elif 'sell_x' in context.user_data:
        percentage = update.message.text
        token_address = context.user_data.pop('sell_x')
        await update.message.reply_text(f"Selling {token_address} worth {percentage}%")
        await process_sell(update, context, percentage)
        context.user_data['expecting_token_amount'] = False

def reset_sniping_context(context):
    context.user_data.pop('expecting_contract_address', None)
    context.user_data.pop('expecting_snipe_amount', None)
    context.user_data.pop('token_address', None)
    context.user_data.pop('buy_amount', None)
    context.user_data.pop('chat_id', None)

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])

if __name__ == '__main__':
    main()
