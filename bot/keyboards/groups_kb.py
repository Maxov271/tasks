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
    )
    kb.add(back_button("dashboard"))
    return kb


def my_groups_list_kb(memberships) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for m in memberships:
        role_emoji = "👑" if m.group.owner_id == m.user_id else ("🧑‍🏫" if m.role_in_group == "mentor" else "🎓")
        kb.add(types.InlineKeyboardButton(f"{role_emoji} {m.group.name}", callback_data=build("group", "view", m.group.id)))
    kb.add(back_button("group:menu"))
    return kb


def group_detail_kb(group, is_owner_or_mentor: bool) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📝 Vazifalar", callback_data=build("group", "tasks", group.id, 0)),
        types.InlineKeyboardButton("👥 A'zolar", callback_data=build("group", "members", group.id, 0)),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Reyting", callback_data=build("group", "leaderboard", group.id)),
        types.InlineKeyboardButton("📢 E'lonlar", callback_data=build("group", "announcements", group.id, 0)),
    )
    if is_owner_or_mentor:
        kb.add(types.InlineKeyboardButton("⚙️ Sozlamalar", callback_data=build("group", "settings", group.id)))
    kb.add(back_button("group:my_list"))
    return kb


def group_tasks_kb(group_id, tasks, page, has_next, is_mentor_or_owner) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for t in tasks:
        emoji = {"homework": "📚", "assignment": "📄", "exam": "🎓"}.get(t.task_type, "📌")
        kb.add(types.InlineKeyboardButton(f"{emoji} {t.title[:35]}", callback_data=build("gtask", "view", t.id)))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=build("group", "tasks", group_id, page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️", callback_data=build("group", "tasks", group_id, page + 1)))
    if nav:
        kb.row(*nav)
    if is_mentor_or_owner:
        kb.add(types.InlineKeyboardButton("➕ Yangi vazifa berish", callback_data=build("gtask", "create", group_id)))
    kb.add(back_button(f"group:view:{group_id}"))
    return kb


def group_members_kb(group_id, members, page, has_next, is_owner) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for m in members:
        role_emoji = "🧑‍🏫" if m.role_in_group == "mentor" else "🎓"
        label = f"{role_emoji} {m.user.display_name}"
        if is_owner:
            kb.add(types.InlineKeyboardButton(label, callback_data=build("group", "member_actions", m.id)))
        else:
            kb.add(types.InlineKeyboardButton(label, callback_data="noop"))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=build("group", "members", group_id, page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️", callback_data=build("group", "members", group_id, page + 1)))
    if nav:
        kb.row(*nav)
    kb.add(back_button(f"group:view:{group_id}"))
    return kb


def member_actions_kb(membership_id, group_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🧑‍🏫 Mentor qilish", callback_data=build("group", "make_mentor", membership_id)),
        types.InlineKeyboardButton("🎓 Studentga qaytarish", callback_data=build("group", "make_student", membership_id)),
    )
    kb.add(types.InlineKeyboardButton("🚪 Guruhdan chiqarish", callback_data=build("group", "remove_member", membership_id)))
    kb.add(back_button(f"group:members:{group_id}:0"))
    return kb


def group_settings_kb(group) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("✏️ Nomini o'zgartirish", callback_data=build("group", "rename", group.id)),
        types.InlineKeyboardButton("📢 E'lon yozish", callback_data=build("group", "post_announcement", group.id)),
        types.InlineKeyboardButton(
            "🔴 Faolsizlantirish" if group.is_active else "🟢 Faollashtirish",
            callback_data=build("group", "toggle_active", group.id),
        ),
    )
    kb.add(back_button(f"group:view:{group.id}"))
    return kb


def announcements_kb(group_id, announcements, page, has_next) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=build("group", "announcements", group_id, page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️", callback_data=build("group", "announcements", group_id, page + 1)))
    if nav:
        kb.row(*nav)
    kb.add(back_button(f"group:view:{group_id}"))
    return kb
