from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, filters
import logging
from database import save_setting, get_all_settings

logging.basicConfig(level=logging.INFO)

# Handlers for displaying and updating settings
async def handle_settings(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    if query:
        await query.answer()

    settings = get_all_settings(user_id)

    keyboard = [
        [InlineKeyboardButton("--- BUY BUTTONS CONFIG ---", callback_data='noop')],
        [InlineKeyboardButton(f"Left: {settings.get('buy_left', '1.0')} CORE", callback_data='edit_buy_buttons_left'),
         InlineKeyboardButton(f"Right: {settings.get('buy_right', '5.0')} CORE", callback_data='edit_buy_buttons_right')],
        [InlineKeyboardButton("--- SELL BUTTONS CONFIG ---", callback_data='noop')],
        [InlineKeyboardButton(f"Left: {settings.get('sell_left', '25')}%", callback_data='edit_sell_buttons_left'),
         InlineKeyboardButton(f"Right: {settings.get('sell_right', '100')}%", callback_data='edit_sell_buttons_right')],
        [InlineKeyboardButton("--- SLIPPAGE CONFIG ---", callback_data='noop')],
        [InlineKeyboardButton(f"Buy: {settings.get('slippage_buy', '10')}%", callback_data='edit_slippage_buy'),
         InlineKeyboardButton(f"Sell: {settings.get('slippage_sell', '10')}%", callback_data='edit_slippage_sell')],
        [InlineKeyboardButton(f"Max Price Impact: {settings.get('max_price_impact', '25')}%", callback_data='edit_max_price_impact')],
        [InlineKeyboardButton("--- MEV PROTECT ---", callback_data='noop')],
        [InlineKeyboardButton("Turbo", callback_data='edit_mev_protect')],
        [InlineKeyboardButton("--- TRANSACTION PRIORITY ---", callback_data='noop')],
        [InlineKeyboardButton("Medium", callback_data='priority_medium'), InlineKeyboardButton("High", callback_data='priority_high')],
        [InlineKeyboardButton("--- SELL PROTECTION ---", callback_data='noop')],
        [InlineKeyboardButton("Enabled", callback_data='edit_sell_protection')],
        [InlineKeyboardButton(f"Minimum Position Value: {settings.get('min_position_value', '1')}", callback_data='edit_min_position_value')],
        [InlineKeyboardButton(f"Maximum Buy Tax: {settings.get('max_buy_tax', '25')} CORE", callback_data='edit_max_buy_tax')],
        [InlineKeyboardButton(f"Maximum Sell Tax: {settings.get('max_sell_tax', '25')}%", callback_data='edit_max_sell_tax')],
        [InlineKeyboardButton("Close", callback_data='back_to_start')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("Settings options:", reply_markup=reply_markup)

# Handlers for button actions
async def handle_edit_buy_buttons_left(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the left buy button value:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'buy_left'

async def handle_edit_buy_buttons_right(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the right buy button value:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'buy_right'

async def handle_edit_sell_buttons_left(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the left sell button value:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'sell_left'

async def handle_edit_sell_buttons_right(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the right sell button value:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'sell_right'

async def handle_edit_slippage_buy(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the slippage for buy without %.\nExample: 1", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'slippage_buy'

async def handle_edit_slippage_sell(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the slippage for sell without %.\nExample: 1", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'slippage_sell'

async def handle_edit_max_price_impact(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the maximum price impact:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'max_price_impact'

async def handle_edit_mev_protect(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("MEV Protect: Turbo enabled.", reply_markup=back_markup('settings'))

async def handle_edit_transaction_priority(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Medium", callback_data='priority_medium')],
        [InlineKeyboardButton("High", callback_data='priority_high')],
        [InlineKeyboardButton("God", callback_data='priority_god')],
        [InlineKeyboardButton("Back", callback_data='settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select the transaction priority:", reply_markup=reply_markup)

async def handle_priority_change(update: Update, context: CallbackContext):
    query = update.callback_query
    priority = query.data.split('_')[1]
    user_id = update.effective_user.id
    save_setting(user_id, 'transaction_priority', priority)
    await query.answer()
    await query.edit_message_text(f"Transaction priority set to {priority}.", reply_markup=back_markup('settings'))

async def handle_edit_min_position_value(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the Minimum Position Value:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'min_position_value'

async def handle_edit_max_buy_tax(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the Maximum Buy Tax:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'max_buy_tax'

async def handle_edit_max_sell_tax(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Enter the Maximum Sell Tax:", reply_markup=back_markup('settings'))
    context.user_data['expecting_setting_value'] = True
    context.user_data['current_setting'] = 'max_sell_tax'

async def save_setting_value(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if context.user_data.get('expecting_setting_value'):
        setting_name = context.user_data['current_setting']
        setting_value = update.message.text
        save_setting(user_id, setting_name, setting_value)
        context.user_data.pop('expecting_setting_value')
        context.user_data.pop('current_setting')
        await update.message.reply_text(f"{setting_name.replace('_', ' ').title()} set to {setting_value}.", reply_markup=back_markup('settings'))

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])
