"""
Tasks bo'limi — to'liq ishlaydigan misol modul. Boshqa handler fayllari
(groups.py, habits.py va h.k.) xuddi shu naqsh (pattern) bo'yicha yoziladi:
1) menyu ko'rsatish, 2) ro'yxat + pagination, 3) detail + amallar, 4) FSM orqali yaratish/tahrirlash.
"""
from django.core.paginator import Paginator
from django.utils import timezone

from apps.tasks.models import Task, SubTask
from services.task_service import complete_task
from bot.keyboards.tasks_kb import (
    tasks_menu_kb, task_list_kb, task_detail_kb, priority_pick_kb,
    deadline_quick_pick_kb, cancel_kb,
)
from bot.utils.formatters import format_task_line, progress_bar
from bot.utils.callback_parser import ParsedCallback
from bot.states.user_states import TaskStates

PAGE_SIZE = 8


def handle_tasks_menu(bot, call, user):
    bot.edit_message_text(
        "📝 Tasks bo'limi. Nima qilmoqchisiz?",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=tasks_menu_kb(),
    )


def _render_task_list(bot, chat_id, message_id, user, page: int, done_filter=None):
    qs = Task.objects.filter(user=user)
    if done_filter is not None:
        qs = qs.filter(is_done=done_filter)
    qs = qs.order_by("deadline")

    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(page + 1)  # Paginator 1-based

    if not page_obj.object_list:
        text = "Bu bo'limda hozircha vazifa yo'q."
    else:
        text = "\n".join(format_task_line(t) for t in page_obj.object_list)

    bot.edit_message_text(
        text,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=task_list_kb(page_obj.object_list, page, page_obj.has_next()),
    )


def handle_task_list(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    _render_task_list(bot, call.message.chat.id, call.message.message_id, user, page)


def handle_task_list_done(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    _render_task_list(bot, call.message.chat.id, call.message.message_id, user, page, done_filter=True)


def handle_task_view(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return

    done, total = task.subtasks_progress
    lines = [f"📌 {task.title}"]
    if task.description:
        lines.append(task.description)
    lines.append(f"⏰ Muddat: {task.deadline.strftime('%d.%m.%Y %H:%M') if task.deadline else 'belgilanmagan'}")
    lines.append(f"Prioritet: {task.priority}")
    if total:
        lines.append(f"Checklist: {progress_bar(done, total)}")

    bot.edit_message_text(
        "\n".join(lines),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=task_detail_kb(task),
    )


def handle_task_done(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    complete_task(task)
    bot.answer_callback_query(call.id, "✅ Bajarildi! XP qo'shildi.")
    handle_task_view(bot, call, user, cb)


def handle_task_create_start(bot, call, user, set_state):
    """Yangi task yaratish — FSM boshlanadi, foydalanuvchidan nom so'raladi."""
    set_state(user.telegram_id, TaskStates.WAITING_TITLE, data={})
    bot.edit_message_text(
        "Vazifa nomini kiriting:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_task_title_input(bot, message, user, state_data, set_state, clear_state):
    title = message.text.strip()
    if not title:
        bot.send_message(message.chat.id, "Nom bo'sh bo'lishi mumkin emas, qayta kiriting:")
        return

    task = Task.objects.create(user=user, title=title)
    clear_state(user.telegram_id)

    bot.send_message(
        message.chat.id,
        f"✅ '{task.title}' vazifasi yaratildi. Endi prioritetni tanlang:",
        reply_markup=priority_pick_kb(task.id),
    )


def handle_set_priority(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    priority = cb.param(1, str)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    task.priority = priority
    task.save(update_fields=["priority"])
    bot.edit_message_text(
        "Prioritet saqlandi. Endi deadline tanlang:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=deadline_quick_pick_kb(task.id),
    )


def handle_set_deadline_quick(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    choice = cb.param(1, str)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return

    now = timezone.localtime()
    if choice == "today":
        task.deadline = now.replace(hour=23, minute=59)
    elif choice == "tomorrow":
        task.deadline = now.replace(hour=23, minute=59) + timezone.timedelta(days=1)
    elif choice == "3d":
        task.deadline = now.replace(hour=23, minute=59) + timezone.timedelta(days=3)
    elif choice == "custom":
        bot.answer_callback_query(call.id, "Sanani DD.MM.YYYY HH:MM formatida yozib yuboring.")
        return  # FSM: WAITING_CUSTOM_DEADLINE holatiga o'tkazish handler chaqiruvchida amalga oshiriladi
    task.save(update_fields=["deadline"])

    bot.answer_callback_query(call.id, "Deadline saqlandi ✅")
    bot.edit_message_text(
        f"🎉 '{task.title}' tayyor!\n⏰ Muddat: {task.deadline.strftime('%d.%m.%Y %H:%M')}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )
