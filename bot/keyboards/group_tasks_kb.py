"""GroupTask (uyga vazifa/topshiriq/imtihon) va TaskSubmission uchun klaviaturalar."""
from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def group_task_detail_kb(group_task, submission, is_mentor_or_owner) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not is_mentor_or_owner:
        if submission is None or submission.status != "graded":
            kb.add(types.InlineKeyboardButton("📎 Topshirish (fayl yuborish)", callback_data=build("gtask", "submit_start", group_task.id)))
    else:
        kb.add(types.InlineKeyboardButton("📥 Topshirilganlar ro'yxati", callback_data=build("gtask", "submissions", group_task.id, 0)))
    kb.add(back_button(f"group:tasks:{group_task.group_id}:0"))
    return kb


def submissions_list_kb(group_task_id, submissions, page, has_next) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    status_emoji = {"pending": "🟡", "graded": "✅", "late": "🔴"}
    for s in submissions:
        emoji = status_emoji.get(s.status, "⚪️")
        kb.add(types.InlineKeyboardButton(f"{emoji} {s.user.display_name}", callback_data=build("gtask", "grade_start", s.id)))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=build("gtask", "submissions", group_task_id, page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("➡️", callback_data=build("gtask", "submissions", group_task_id, page + 1)))
    if nav:
        kb.row(*nav)
    kb.add(back_button(f"gtask:view:{group_task_id}"))
    return kb


def gtask_type_pick_kb(group_id) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("📚 Uyga vazifa", callback_data=build("gtask", "set_type", group_id, "homework")),
        types.InlineKeyboardButton("📄 Topshiriq", callback_data=build("gtask", "set_type", group_id, "assignment")),
        types.InlineKeyboardButton("🎓 Imtihon", callback_data=build("gtask", "set_type", group_id, "exam")),
    )
    return kb
