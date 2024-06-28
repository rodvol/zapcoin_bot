from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import json
from database import get_user_address, get_user_private_key
import logging
logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler()
scheduler.start()

async def handle_dca(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.message.reply_text("Paste the Contract Address you’d like to DCA")
    context.user_data['expecting_dca_address'] = True

async def handle_dca_address(update: Update, context: CallbackContext):
    token_address = update.message.text
    context.user_data['dca_token_address'] = token_address
    context.user_data['expecting_dca_address'] = False
    await update.message.reply_text("Input the Amount of CORE you’d like to snipe with")
    context.user_data['expecting_dca_amount'] = True

async def handle_dca_amount(update: Update, context: CallbackContext):
    amount = update.message.text
    context.user_data['dca_amount'] = amount
    context.user_data['expecting_dca_amount'] = False
    await update.message.reply_text("Input how frequently (In days) you’d like to DCA")
    context.user_data['expecting_dca_frequency'] = True

async def handle_dca_frequency(update: Update, context: CallbackContext):
    frequency = update.message.text
    context.user_data['dca_frequency'] = frequency
    context.user_data['expecting_dca_frequency'] = False

    # Schedule the first DCA task
    user_id = update.effective_user.id
    start_date = datetime.now() + timedelta(days=int(frequency))
    job = scheduler.add_job(execute_dca, 'interval', days=int(frequency), args=[user_id, context], next_run_time=start_date)
    context.user_data['dca_job_id'] = job.id

    await update.message.reply_text(f"Started DCA’ing. The First DCA Transaction will happen in {frequency} days",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel DCA'ing", callback_data='cancel_dca')]]))

async def execute_dca(user_id, context):
    token_address = context.user_data['dca_token_address']
    amount = context.user_data['dca_amount']
    address = get_user_address(user_id)
    private_key = get_user_private_key(user_id)
    from navigation_handlers import (buy_token)

    try:
        tx_hash, _ = await buy_token(address, token_address, float(amount), private_key)
        await context.bot.send_message(chat_id=user_id,
                                       text=f"Your order to conduct DCA for the {token_address} in {context.user_data['dca_frequency']} days has been conducted.\nTransaction Hash: {tx_hash}",
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel DCA’ing", callback_data='cancel_dca')]]))
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"DCA transaction failed: {str(e)}")

async def handle_cancel_dca(update: Update, context: CallbackContext):
    query = update.callback_query
    job_id = context.user_data.get('dca_job_id')
    if job_id:
        scheduler.remove_job(job_id)
        del context.user_data['dca_job_id']
        await query.edit_message_text("Your DCA Request has been canceled successfully")
    else:
        await query.edit_message_text("No active DCA to cancel.")

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])
