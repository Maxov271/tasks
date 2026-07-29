from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def tasks_menu_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Yangi vazifa", callback_data=build("task", "create")),
        types.InlineKeyboardButton("📋 Barchasi", callback_data=build("task", "list", 0)),
    )
    kb.add(
        types.InlineKeyboardButton("✅ Bajarilgan", callback_data=build("task", "list_done", 0)),
        types.InlineKeyboardButton("⏰ Muddati yaqin", callback_data=build("task", "list_upcoming", 0)),
    )
    kb.add(
        types.InlineKeyboardButton("📁 Kategoriyalar", callback_data=build("task", "categories")),
        types.InlineKeyboardButton("🔍 Qidirish", callback_data=build("task", "search")),
    )
    kb.add(back_button("dashboard"))
    return kb


def task_list_kb(tasks, page: int, has_next: bool, back_target: str = "task:menu") -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for t in tasks:
        # Rangli holat belgisi: 🔴 muddati o'tgan, ✅ bajarilgan, prioritet rangiga qarab ochiq
        if t.is_done:
            marker = "✅"
        elif t.is_overdue:
            marker = "🔴"
        else:
            marker = {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"}.get(t.priority, "⚪️")
        kb.add(types.InlineKeyboardButton(f"{marker} {t.title[:35]}", callback_data=build("task", "view", t.id)))

    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton("⬅️", callback_data=build("task", "list", page - 1)))
    if has_next:
        nav_row.append(types.InlineKeyboardButton("➡️", callback_data=build("task", "list", page + 1)))
    if nav_row:
        kb.row(*nav_row)

    kb.add(back_button(back_target))
    return kb


def task_detail_kb(task) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    if not task.is_done:
        kb.add(types.InlineKeyboardButton("✅ Bajarildi deb belgilash", callback_data=build("task", "done", task.id)))
    kb.add(
        types.InlineKeyboardButton("✏️ Tahrirlash", callback_data=build("task", "edit", task.id)),
        types.InlineKeyboardButton("🗑 O'chirish", callback_data=build("task", "delete_confirm", task.id)),
    )
    kb.add(types.InlineKeyboardButton("☑️ Subtasklar", callback_data=build("task", "subtasks", task.id)))
    kb.add(back_button("task:list:0"))
    return kb


def task_edit_menu_kb(task_id) -> types.InlineKeyboardMarkup:
    """Tahrirlash bo'limi — nima o'zgartirilishini tanlash menyusi."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✏️ Nomi", callback_data=build("task", "edit_title", task_id)),
        types.InlineKeyboardButton("📝 Tavsifi", callback_data=build("task", "edit_desc", task_id)),
    )
    kb.add(
        types.InlineKeyboardButton("🚦 Prioritet", callback_data=build("task", "edit_priority", task_id)),
        types.InlineKeyboardButton("⏰ Deadline", callback_data=build("task", "edit_deadline", task_id)),
    )
    kb.add(back_button(f"task:view:{task_id}"))
    return kb


def task_delete_confirm_kb(task_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🗑 Ha, o'chirish", callback_data=build("task", "delete", task_id)),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data=build("task", "view", task_id)),
    )
    return kb


def priority_pick_kb(task_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.add(
        types.InlineKeyboardButton("🟢 Past", callback_data=build("task", "set_priority", task_id, "low")),
        types.InlineKeyboardButton("🟡 O'rta", callback_data=build("task", "set_priority", task_id, "medium")),
        types.InlineKeyboardButton("🟠 Yuqori", callback_data=build("task", "set_priority", task_id, "high")),
        types.InlineKeyboardButton("🔴 Zudlik", callback_data=build("task", "set_priority", task_id, "urgent")),
    )
    return kb


def deadline_quick_pick_kb(task_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📅 Bugun", callback_data=build("task", "set_deadline", task_id, "today")),
        types.InlineKeyboardButton("📅 Ertaga", callback_data=build("task", "set_deadline", task_id, "tomorrow")),
    )
    kb.add(
        types.InlineKeyboardButton("📅 3 kun", callback_data=build("task", "set_deadline", task_id, "3d")),
        types.InlineKeyboardButton("✍️ Sana kiritish", callback_data=build("task", "set_deadline", task_id, "custom")),
    )
    kb.add(types.InlineKeyboardButton("✅ Deadline'siz saqlash", callback_data=build("task", "view", task_id)))
    return kb


def subtasks_kb(task) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for st in task.subtasks.all():
        mark = "✅" if st.is_done else "⬜️"
        kb.add(types.InlineKeyboardButton(f"{mark} {st.title[:40]}", callback_data=build("task", "toggle_subtask", st.id)))
    kb.add(types.InlineKeyboardButton("➕ Subtask qo'shish", callback_data=build("task", "add_subtask", task.id)))
    kb.add(back_button(f"task:view:{task.id}"))
    return kb


def categories_kb(categories) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for c in categories:
        kb.add(types.InlineKeyboardButton(f"🎨 {c.name}", callback_data=build("task", "list_by_category", c.id, 0)))
    kb.add(types.InlineKeyboardButton("➕ Yangi kategoriya", callback_data=build("task", "create_category")))
    kb.add(back_button("task:menu"))
    return kb


def cancel_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data=build("nav", "cancel")))
    return kb
