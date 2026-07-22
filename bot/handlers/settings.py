"""Settings/Profile bo'limi."""
from telebot import types
from bot.utils.callback_parser import build


def settings_menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🌐 Til", callback_data=build("settings", "language")),
        types.InlineKeyboardButton("🔔 Bildirishnomalar", callback_data=build("notif", "menu")),
    )
    return kb


def handle_settings_menu(bot, call, user):
    bot.edit_message_text(
        "⚙️ Sozlamalar", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=settings_menu_kb(),
    )


def handle_profile_menu(bot, call, user):
    level_info = getattr(user, "level_info", None)
    text = (
        f"👤 {user.display_name}\n"
        f"🌐 Til: {user.language}\n"
        f"⭐ Premium: {'Ha' if user.is_premium else 'Yo\u02bbq'}\n"
        f"🏆 Level: {level_info.level if level_info else 1}"
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id)
