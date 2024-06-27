from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from liquidity_sniping import start_liquidity_sniping_task, stop_liquidity_sniping_task, sniping_tasks
import logging
logging.basicConfig(level=logging.INFO)

async def handle_liquidity_sniping(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Start Sniping", callback_data='start_liquidity_sniping')],
        [InlineKeyboardButton("Stop Sniping", callback_data='stop_liquidity_sniping')],
        [InlineKeyboardButton("Back", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Liquidity Sniping options:", reply_markup=reply_markup)

async def handle_start_liquidity_sniping(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id

    if user_id in sniping_tasks:
        await query.edit_message_text("Liquidity sniping is already running.", reply_markup=back_markup('liquidity_sniping'))
        return

    await query.edit_message_text("Please enter the token contract address:", reply_markup=back_markup('liquidity_sniping'))
    context.user_data['liquidity_sniping_token_address'] = True

async def handle_stop_liquidity_sniping(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    await stop_liquidity_sniping_task(user_id)
    await query.edit_message_text("Liquidity sniping stopped.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_to_start')]]))

async def handle_stop_sniping_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = int(query.data.split('_')[-1])
    await query.answer()
    await stop_liquidity_sniping_task(user_id)
    await query.edit_message_text("Liquidity sniping stopped.", reply_markup=back_markup('liquidity_sniping'))

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])
