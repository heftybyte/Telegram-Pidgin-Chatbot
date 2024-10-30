import os
import aiohttp
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def get_user_telegram_info(update: Update):
    user = update.effective_user
    info = {
        "user_id": user.id,
        "username": user.username,
        "name": f"{user.first_name} {user.last_name}",
        "language": user.language_code,
        "is_bot": user.is_bot
    }
    return info


async def create_chat_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a chat session"""
    user_data = await get_user_telegram_info(update)
    async with aiohttp.ClientSession() as session:
        async with session.post(os.getenv("API_URL") + "/create-session", json=user_data) as response:
            if response.status == 200:
                chat_session = await response.json()
                context.user_data['threshold'] = chat_session['threshold']
                context.user_data['accepted_policy'] = False
                context.user_data['user_id'] = user_data['user_id']
                return True
            else:
                return False



async def get_model_response(context: ContextTypes.DEFAULT_TYPE, update: Update):
    """Get model response"""
    print({
            "user_id": update.effective_user.id,
            "message": update.message.text
        })
    async with aiohttp.ClientSession() as session:
        async with session.post(os.getenv("API_URL") + "/send-message", json={
            "user_id": str(update.effective_user.id),
            "message": update.message.text
        }) as response:
            if response.status == 200:
                model_response = await response.json()
                return model_response
            else:
                return False


async def get_user_data(user_id: str):
    """Get user info"""
    async with aiohttp.ClientSession() as session:
        async with session.get(os.getenv("API_URL") + "/get-user-info", params={"user_id": user_id}) as response:
            if response.status == 200:
                user_data = await response.json()
                user_info = user_data['user_info']
                user_information = {
                    "user_id": user_info[0],
                    "threshold": user_info[1],
                    "chat_history": user_info[2],
                    "user_info": user_info[3],
                    "accepted_policy": user_info[4]
                }
                return user_information
            else:
                return False


async def update_user_privacy_policy_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user privacy policy acceptance"""
    user_data = await get_user_telegram_info(update)
    async with aiohttp.ClientSession() as session:
        async with session.post(os.getenv("API_URL") + "/accept-policy", params={"user_id": user_data['user_id']}) as response:
            if response.status == 200:
                return True
            else:
                return False
