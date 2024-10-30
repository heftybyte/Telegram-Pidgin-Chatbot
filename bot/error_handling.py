import logging
from telegram.error import Conflict
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    if isinstance(context.error, Conflict):
        logger.error("Conflict error: Another instance of the bot is already running.")
        # You might want to exit the program here
        import sys
        sys.exit(1)