from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def achievements_menu_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🏅 Mening badgelarim", callback_data=build("ach", "my_badges")),
        types.InlineKeyboardButton("📊 Level va XP", callback_data=build("ach", "level_info")),
    )
    kb.add(
        types.InlineKeyboardButton("🏆 Reyting", callback_data=build("ach", "leaderboard", "all_time")),
        types.InlineKeyboardButton("🎯 Keyingi maqsad", callback_data=build("ach", "next_goal")),
    )
    kb.add(back_button("dashboard"))
    return kb


def leaderboard_period_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.add(
        types.InlineKeyboardButton("Kunlik", callback_data=build("ach", "leaderboard", "daily")),
        types.InlineKeyboardButton("Haftalik", callback_data=build("ach", "leaderboard", "weekly")),
        types.InlineKeyboardButton("Oylik", callback_data=build("ach", "leaderboard", "monthly")),
        types.InlineKeyboardButton("Umumiy", callback_data=build("ach", "leaderboard", "all_time")),
    )
    return kb
