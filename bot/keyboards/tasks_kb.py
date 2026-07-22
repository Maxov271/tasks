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


def task_list_kb(tasks, page: int, has_next: bool) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for t in tasks:
        label = f"{'✅' if t.is_done else '🔹'} {t.title[:35]}"
        kb.add(types.InlineKeyboardButton(label, callback_data=build("task", "view", t.id)))

    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton("⬅️", callback_data=build("task", "list", page - 1)))
    if has_next:
        nav_row.append(types.InlineKeyboardButton("➡️", callback_data=build("task", "list", page + 1)))
    if nav_row:
        kb.row(*nav_row)

    kb.add(back_button("task:menu"))
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


def priority_pick_kb(task_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.add(
        types.InlineKeyboardButton("🟢", callback_data=build("task", "set_priority", task_id, "low")),
        types.InlineKeyboardButton("🟡", callback_data=build("task", "set_priority", task_id, "medium")),
        types.InlineKeyboardButton("🟠", callback_data=build("task", "set_priority", task_id, "high")),
        types.InlineKeyboardButton("🔴", callback_data=build("task", "set_priority", task_id, "urgent")),
    )
    return kb


def deadline_quick_pick_kb(task_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Bugun", callback_data=build("task", "set_deadline", task_id, "today")),
        types.InlineKeyboardButton("Ertaga", callback_data=build("task", "set_deadline", task_id, "tomorrow")),
    )
    kb.add(
        types.InlineKeyboardButton("3 kun", callback_data=build("task", "set_deadline", task_id, "3d")),
        types.InlineKeyboardButton("📅 Sana kiritish", callback_data=build("task", "set_deadline", task_id, "custom")),
    )
    return kb


def cancel_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data=build("nav", "cancel")))
    return kb
