# bot/keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.text_utils import get_text


def get_main_menu_keyboard(script: str = "latin") -> InlineKeyboardMarkup:
    new_interview_text = get_text("button_new_interview_uznetix", script)
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=new_interview_text,
            callback_data="start_interview"
        )]
    ])


