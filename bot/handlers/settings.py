"""Settings/Profile bo'limi — til tanlash bilan birga."""
from telebot import types
from bot.utils.callback_parser import build
from bot.utils.callback_parser import ParsedCallback


def settings_menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🌐 Til", callback_data=build("settings", "language")),
        types.InlineKeyboardButton("🔔 Bildirishnomalar", callback_data=build("notif", "menu")),
    )
    from bot.keyboards.dashboard_kb import back_button
    kb.add(back_button("dashboard"))
    return kb


def language_pick_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data=build("settings", "set_language", "uz")),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data=build("settings", "set_language", "ru")),
        types.InlineKeyboardButton("🇬🇧 English", callback_data=build("settings", "set_language", "en")),
    )
    from bot.keyboards.dashboard_kb import back_button
    kb.add(back_button("settings:menu"))
    return kb


def handle_settings_menu(bot, call, user):
    bot.edit_message_text(
        "⚙️ Sozlamalar", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=settings_menu_kb(),
    )


def handle_language_menu(bot, call, user):
    bot.edit_message_text(
        f"🌐 Joriy til: {user.language}. Yangi tilni tanlang:",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=language_pick_kb(),
    )


def handle_set_language(bot, call, user, cb: ParsedCallback):
    lang = cb.param(0, str, "uz")
    user.language = lang
    user.save(update_fields=["language"])
    bot.answer_callback_query(call.id, "✅ Til saqlandi.")
    handle_settings_menu(bot, call, user)


def handle_profile_menu(bot, call, user):
    from bot.keyboards.dashboard_kb import back_button
    level_info = getattr(user, "level_info", None)
    text = (
        f"👤 {user.display_name}\n"
        f"🌐 Til: {user.language}\n"
        f"⭐ Premium: {'Ha' if user.is_premium else 'Yo\u02bbq'}\n"
        f"🏆 Level: {level_info.level if level_info else 1}"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(back_button("dashboard"))
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
