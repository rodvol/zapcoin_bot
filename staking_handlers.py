from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging
logging.basicConfig(level=logging.INFO)

async def handle_stake(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("How many $CORE would you like to stake?", reply_markup=back_markup('back_to_start'))
    context.user_data['staking'] = True

async def handle_confirm_stake(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "We only support Everstake Validator at the moment. Are you okay with it? If Yes please proceed and tap on ‘Continue’\n"
        "For More details about Everstake and APY-related information check it out: https://stake.coredao.org/validator/0x307f36ff0aff7000ebd4eea1e8e9bbbfa0e1134c",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Continue", callback_data='confirm_stake')],
            [InlineKeyboardButton("Back", callback_data='back_to_start')]
        ])
    )

async def handle_claim(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    # Assuming claim logic here
    await query.edit_message_text("Claiming <Amount of CORE>")
    # Simulate successful claim
    await query.edit_message_text("Claimed <Amount of CORE>\nTransaction Hash: <Tx hash>", reply_markup=back_markup('back_to_start'))

def back_markup(previous_menu):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=previous_menu)]])
