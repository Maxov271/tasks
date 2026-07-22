from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def admin_menu_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Userlar", callback_data=build("admin", "users", 0)),
        types.InlineKeyboardButton("👥 Guruhlar", callback_data=build("admin", "groups", 0)),
    )
    kb.add(
        types.InlineKeyboardButton("📢 Broadcast", callback_data=build("admin", "broadcast")),
        types.InlineKeyboardButton("📊 Statistika", callback_data=build("admin", "stats")),
    )
    kb.add(
        types.InlineKeyboardButton("💾 Backup", callback_data=build("admin", "backup")),
        types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data=build("admin", "settings")),
    )
    kb.add(back_button("dashboard"))
    return kb


def user_admin_actions_kb(user_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🚫 Ban", callback_data=build("admin", "ban", user_id)),
        types.InlineKeyboardButton("✅ Unban", callback_data=build("admin", "unban", user_id)),
    )
    kb.add(
        types.InlineKeyboardButton("⭐ Premium berish", callback_data=build("admin", "grant_premium", user_id)),
        types.InlineKeyboardButton("👥 Guruh ruxsati", callback_data=build("admin", "allow_group", user_id)),
    )
    kb.add(back_button("admin:users:0"))
    return kb
