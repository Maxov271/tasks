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
    )
    kb.add(back_button("dashboard"))
    return kb


def admin_users_list_kb(users, page, has_next) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for u in users:
        marker = "🚫" if u.is_banned else ("⭐" if u.is_premium else "👤")
        kb.add(types.InlineKeyboardButton(f"{marker} {u.display_name}", callback_data=build("admin", "user_detail", u.id)))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=build("admin", "users", page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️", callback_data=build("admin", "users", page + 1)))
    if nav:
        kb.row(*nav)
    kb.add(back_button("admin:menu"))
    return kb


def user_admin_actions_kb(target) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    if target.is_banned:
        kb.add(types.InlineKeyboardButton("✅ Unban", callback_data=build("admin", "unban", target.id)))
    else:
        kb.add(types.InlineKeyboardButton("🚫 Ban", callback_data=build("admin", "ban", target.id)))
    kb.add(types.InlineKeyboardButton(
        "⭐ Premiumni bekor qilish" if target.is_premium else "⭐ Premium berish",
        callback_data=build("admin", "toggle_premium", target.id),
    ))
    kb.add(types.InlineKeyboardButton(
        "🚫 Guruh ruxsatini olish" if target.can_create_group else "👥 Guruh ruxsatini berish",
        callback_data=build("admin", "toggle_group_perm", target.id),
    ))
    kb.add(back_button("admin:users:0"))
    return kb


def admin_groups_list_kb(groups, page, has_next) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for g in groups:
        marker = "🟢" if g.is_active else "🔴"
        kb.add(types.InlineKeyboardButton(f"{marker} {g.name} ({g.active_members_count})", callback_data=build("group", "view", g.id)))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=build("admin", "groups", page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️", callback_data=build("admin", "groups", page + 1)))
    if nav:
        kb.row(*nav)
    kb.add(back_button("admin:menu"))
    return kb
