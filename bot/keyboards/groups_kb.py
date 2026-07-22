from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def groups_menu_kb(can_create: bool) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("📚 Mening guruhlarim", callback_data=build("group", "my_list")))
    if can_create:
        kb.add(types.InlineKeyboardButton("➕ Guruh yaratish", callback_data=build("group", "create")))
    kb.add(
        types.InlineKeyboardButton("🔑 Kodga qo'shilish", callback_data=build("group", "join_by_code")),
        types.InlineKeyboardButton("📢 E'lonlar", callback_data=build("group", "announcements")),
    )
    kb.add(back_button("dashboard"))
    return kb


def group_detail_kb(group, is_owner_or_mentor: bool) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📝 Vazifalar", callback_data=build("group", "tasks", group.id)),
        types.InlineKeyboardButton("👥 A'zolar", callback_data=build("group", "members", group.id, 0)),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Reyting", callback_data=build("group", "leaderboard", group.id)),
    )
    if is_owner_or_mentor:
        kb.add(types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data=build("group", "settings", group.id)))
    kb.add(back_button("group:my_list"))
    return kb
