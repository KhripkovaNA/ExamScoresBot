from typing import List, Tuple
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def choose_subject_kb(subjects: List[str]) -> InlineKeyboardMarkup:
    subject_buttons = [
        [
            InlineKeyboardButton(text=subject, callback_data=subject)
        ] for subject in subjects
    ]
    button_cancel = [InlineKeyboardButton(text="Отмена", callback_data="Отмена")]
    subject_buttons.append(button_cancel)
    markup = InlineKeyboardMarkup(
        inline_keyboard=subject_buttons
    )
    return markup


def confirm_kb() -> InlineKeyboardMarkup:
    button_yes = InlineKeyboardButton(text="Да", callback_data="да")
    button_no = InlineKeyboardButton(text="Нет", callback_data="нет")
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[button_yes, button_no]]
    )
    return markup
