import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

from bot import error_handler, create_chat_session, get_model_response
from bot.handlers import get_user_data, update_user_privacy_policy_acceptance

load_dotenv()

# Enable logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Yes, I don hear", callback_data="yes"),
            InlineKeyboardButton("No, I no do", callback_data="no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup



async def send_typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send typing action to user"""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)



async def policy_message(update: Update, user_data):
    # check if user has not accepted the policy and send them the policy
    if user_data and not user_data['accepted_policy']:
        reply_markup = keyboard()
        await update.message.reply_text("Welcome oh! I greet you. Before we start abeg, make we yarn small about privacy.\n\nAs we dey talk, I fit dey collect small data wey go help me learn. No fear, I no go cast your gist. If you wan know as e dey go, enter here make you read the full gist: https://www.google.com", reply_markup=reply_markup)
    # if user has accepted the policy, send them a welcome message
    elif user_data and user_data['accepted_policy']:
        await update.message.reply_text(f"""How you dey @{update.message.chat.username}? Abeg, follow me talk, na only Pidgin I sabi. Wetin dey happen for Nigeria?""")



async def accept_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Accept the policy"""

    print(f"Context user data: {context.user_data}")

    user_id = update.effective_user.id
    user_data = await get_user_data(user_id)
    print(f"User data: {user_data}")
    # if user exists
    if user_data:
        print('user data exists')
        # check if user has accepted the policy and send them a welcome message if they have 
        await policy_message(update, user_data)
    else:
        print('user data does not exist')
        # if user does not exist, create a new user and send them the policy if they have not accepted it
        if await create_chat_session(update, context):
            user_data = await get_user_data(user_id)
            await policy_message(update, user_data)
        else:
            await update.message.reply_text("Failed to create chat session")
            logger.error("Failed to create chat session")


    

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery after the user clicks a button"""

    query = update.callback_query

    await query.answer()

    if query.data == "yes":
        if await update_user_privacy_policy_acceptance(update, context):
            context.user_data['accepted_policy'] = True
            await query.edit_message_text(text="You sabi better thing! Make we continue.")    
    else:
        context.user_data['accepted_policy'] = False
        await query.edit_message_text(text="Oya na, Kachifo!")



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the start message"""

    # Send typing action to user - to show that the bot is typing
    await send_typing_action(update, context)

    logger.info(f"{update.message.chat.id} - {update.message.chat.username} - {update.message.text}")

    # Ask user to accept policy first
    await accept_policy(update, context)
    


async def get_response_send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get response from model and send reply to user"""

    model_response = await get_model_response(context, update)
    print(f"Model response: {model_response}")
    if model_response:
        await update.message.reply_text(f"{model_response['message']}")
        context.user_data['threshold'] = model_response['threshold']
    else:
        await update.effective_chat.send_message("Omo, e be like something don spoil, try again")
        logger.error("Failed to get model response")



async def handle_message(update, context):
    """Handle user message."""

    # Send typing action to user - to show that the bot is typing
    await send_typing_action(update, context)

    print(f"Context user data in handle_message: {context.user_data}")
    try:
        user_id = update.effective_user.id
        user_data = await get_user_data(user_id)
        if user_data and not user_data['accepted_policy']:
            print('accepted policy is false in user data', user_data)
            await accept_policy(update, context)
        # if user has accepted the policy, continue with the chat session
        else:
            print('accepted policy is true in user data', user_data)
            if update.message and update.message.text:
                await get_response_send_reply(update, context)

        
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        # Optionally, inform the user about the error
        await update.effective_chat.send_message("Wahala dey oh, you go wait small abeg, make I check wetin sup.")



def main():
    """Run the bot."""

    # Get the token from the environment variables
    token = os.getenv("TELEGRAM_TOKEN")

    # Check if the token is exists
    if token is None:
        logger.error("TELEGRAM_TOKEN is not set")
        raise ValueError("TELEGRAM_TOKEN is not set")
    
    # Create the application and pass it your bot's token.
    application = ApplicationBuilder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("yes", accept_policy))
    application.add_handler(CommandHandler("no", accept_policy))
    application.add_error_handler(error_handler)
 
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()
