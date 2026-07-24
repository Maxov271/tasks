from telebot import types
from bot.utils.callback_parser import build


def main_dashboard_kb(is_admin: bool = False) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 Dashboard", callback_data=build("nav", "open", "dashboard")),
        types.InlineKeyboardButton("📝 Tasks", callback_data=build("task", "menu")),
    )
    kb.add(
        types.InlineKeyboardButton("👥 Groups", callback_data=build("group", "menu")),
        types.InlineKeyboardButton("📈 Statistics", callback_data=build("stats", "menu")),
    )
    kb.add(
        types.InlineKeyboardButton("🔥 Habits", callback_data=build("habit", "menu")),
        types.InlineKeyboardButton("🎯 Focus Mode", callback_data=build("focus", "menu")),
    )
    kb.add(
        types.InlineKeyboardButton("🏆 Achievements", callback_data=build("ach", "menu")),
        types.InlineKeyboardButton("⚙️ Settings", callback_data=build("settings", "menu")),
    )
    kb.add(
        types.InlineKeyboardButton("👤 Profile", callback_data=build("profile", "menu")),
        types.InlineKeyboardButton("🔔 Notifications", callback_data=build("notif", "menu")),
    )
    kb.add(
        types.InlineKeyboardButton("📅 Calendar", callback_data=build("calendar", "menu")),
    )
    if is_admin:
        kb.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data=build("admin", "menu")))
    return kb


def back_button(target: str = "dashboard") -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton("⬅️ Orqaga", callback_data=build("nav", "back", target))
