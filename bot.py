import os
import aiohttp
from dotenv import load_dotenv
from telegram.error import Conflict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ContextTypes
from telegram.constants import ChatAction

load_dotenv()

# Enable logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    if isinstance(context.error, Conflict):
        logger.error("Conflict error: Another instance of the bot is already running.")
        # You might want to exit the program here
        import sys
        sys.exit(1)


async def create_chat_session(context: ContextTypes.DEFAULT_TYPE):
    """Create a chat session"""
    async with aiohttp.ClientSession() as session:
        async with session.post(os.getenv("API_URL") + "/create-session") as response:
            if response.status == 200:
                chat_session = await response.json()
                logger.info(f"Chat session: {chat_session}")
                context.user_data['session_id'] = chat_session['session_id']
                context.user_data['threshold'] = chat_session['threshold']
                return True
            else:
                return False


async def get_model_response(context: ContextTypes.DEFAULT_TYPE, update: Update):
    """Get model response"""
    async with aiohttp.ClientSession() as session:
        async with session.post(os.getenv("API_URL") + "/send-message", json={
            "session_id": context.user_data['session_id'],
            "message": update.message.text
        }) as response:
            if response.status == 200:
                model_response = await response.json()
                return model_response
            else:
                return False
                

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the start message"""

    # Send typing action to user - to show that the bot is typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    logger.info(f"{update.message.chat.id} - {update.message.chat.username} - {update.message.text}")
    
    # Create chat session if not in context.user_data
    if 'session_id' not in context.user_data:
        if await create_chat_session(context):
            logger.info(f"user context data: {context.user_data}")
            # Send message to user
            await update.message.reply_text(f"""How you dey @{update.message.chat.username}? Abeg, follow me talk, na only Pidgin I sabi. Wetin dey happen for Nigeria?""")
        else:
            await update.message.reply_text("Failed to create chat session")
            logger.error("Failed to create chat session")
    else:
        logger.info(f"Chat session already exists: {context.user_data}")
        # Send message to user
        await update.message.reply_text(f"""How far na @{update.message.chat.username}? I dey with you""")


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
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    print(f"Context user data: {context.user_data}")
    try:
        if 'session_id' not in context.user_data:
            if await create_chat_session(context):
                if update.message and update.message.text:
                    await get_response_send_reply(update, context)
            else:
                logger.error("Failed to create chat session")
        else:
            if update.message and update.message.text:
                await get_response_send_reply(update, context)

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        # Optionally, inform the user about the error
        await update.effective_chat.send_message("Sorry, an error occurred while processing your message.")



# async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Parses the CallbackQuery after the user clicks a button"""

#     query = update.callback_query

#     # CallbackQueries need to be answered, even if no notification to the user is needed
#     # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
#     await query.answer()

#     await query.edit_message_text(text=f"Selected option: {query.data}")


# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Displays info on how to use the bot."""

#     # CREATE BUTTON
#     keyboard = [
#         [
#             InlineKeyboardButton("Help", callback_data="help")
#         ]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     # SEND MESSAGE WITH BUTTON
#     await update.message.reply_text(f"""Be like say you don confuse""", reply_markup=reply_markup)



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
    # application.add_handler(CallbackQueryHandler(button))
    # application.add_handler(CommandHandler("help", help_command))
    application.add_error_handler(error_handler)
 
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()
