from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def habits_menu_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Yangi odat", callback_data=build("habit", "create")),
        types.InlineKeyboardButton("✅ Bugungi belgilash", callback_data=build("habit", "check_today")),
    )
    kb.add(
        types.InlineKeyboardButton("📈 Statistika", callback_data=build("habit", "stats")),
        types.InlineKeyboardButton("🗑 O'chirish", callback_data=build("habit", "delete_list")),
    )
    kb.add(back_button("dashboard"))
    return kb


def habit_delete_list_kb(habits) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for h in habits:
        kb.add(types.InlineKeyboardButton(f"🗑 {h.icon_emoji} {h.name}", callback_data=build("habit", "delete", h.id)))
    kb.add(back_button("habit:menu"))
    return kb
