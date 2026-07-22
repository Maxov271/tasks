from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def focus_menu_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("▶️ 25 daqiqa", callback_data=build("focus", "start", 25)),
        types.InlineKeyboardButton("▶️ 50 daqiqa", callback_data=build("focus", "start", 50)),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Bugungi fokus", callback_data=build("focus", "today_stats")),
        types.InlineKeyboardButton("📅 Haftalik hisobot", callback_data=build("focus", "weekly_report")),
    )
    kb.add(back_button("dashboard"))
    return kb


def focus_active_kb(session_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⏸ To'xtatish", callback_data=build("focus", "stop", session_id)))
    return kb
