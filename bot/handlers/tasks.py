"""
Tasks bo'limi — to'liq ishlaydigan modul (menu -> list -> detail -> edit/delete/subtasks/categories/search).
"""
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from apps.tasks.models import Task, SubTask, Category
from services.task_service import complete_task
from bot.keyboards.tasks_kb import (
    tasks_menu_kb, task_list_kb, task_detail_kb, task_edit_menu_kb, task_delete_confirm_kb,
    priority_pick_kb, deadline_quick_pick_kb, subtasks_kb, categories_kb, cancel_kb,
)
from bot.utils.formatters import format_task_line, progress_bar
from bot.utils.callback_parser import ParsedCallback
from bot.states.user_states import TaskStates

PAGE_SIZE = 8


# ---------------------------------------------------------------------------
# Menu / list / detail
# ---------------------------------------------------------------------------

def handle_tasks_menu(bot, call, user):
    bot.edit_message_text(
        "📝 Tasks bo'limi. Nima qilmoqchisiz?",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=tasks_menu_kb(),
    )


def _render_task_list(bot, chat_id, message_id, user, page: int, done_filter=None,
                       upcoming_only=False, category_id=None, back_target="task:menu"):
    qs = Task.objects.filter(user=user)
    if done_filter is not None:
        qs = qs.filter(is_done=done_filter)
    if upcoming_only:
        qs = qs.filter(is_done=False, deadline__isnull=False).order_by("deadline")
    else:
        qs = qs.order_by("deadline")
    if category_id is not None:
        qs = qs.filter(category_id=category_id)

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
        reply_markup=task_list_kb(page_obj.object_list, page, page_obj.has_next(), back_target=back_target),
    )


def handle_task_list(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    _render_task_list(bot, call.message.chat.id, call.message.message_id, user, page)


def handle_task_list_done(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    _render_task_list(bot, call.message.chat.id, call.message.message_id, user, page, done_filter=True)


def handle_task_list_upcoming(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    _render_task_list(bot, call.message.chat.id, call.message.message_id, user, page, upcoming_only=True)


def handle_task_view(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return

    done, total = task.subtasks_progress
    priority_label = {"low": "🟢 Past", "medium": "🟡 O'rta", "high": "🟠 Yuqori", "urgent": "🔴 Zudlik bilan"}.get(task.priority, task.priority)
    lines = [f"📌 {task.title}"]
    if task.description:
        lines.append(task.description)
    lines.append(f"⏰ Muddat: {task.deadline.strftime('%d.%m.%Y %H:%M') if task.deadline else 'belgilanmagan'}" + ("  🔴 MUDDATI O'TGAN" if task.is_overdue else ""))
    lines.append(f"Prioritet: {priority_label}")
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


# ---------------------------------------------------------------------------
# Yaratish (FSM)
# ---------------------------------------------------------------------------

def handle_task_create_start(bot, call, user, set_state):
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

    # Agar kalendardan "shu kunga vazifa qo'shish" orqali kelingan bo'lsa, deadline avtomatik o'rnatiladi
    prefill = state_data.get("prefill_deadline") if state_data else None
    if prefill:
        try:
            y, m, d = (int(p) for p in prefill.split("-"))
            task.deadline = timezone.make_aware(datetime(y, m, d, 23, 59))
            task.save(update_fields=["deadline"])
        except (ValueError, TypeError):
            pass

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
        "Prioritet saqlandi ✅. Endi deadline tanlang:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=deadline_quick_pick_kb(task.id),
    )


def handle_set_deadline_quick(bot, call, user, cb: ParsedCallback, set_state):
    task_id = cb.param(0, int)
    choice = cb.param(1, str)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return

    if choice == "custom":
        set_state(user.telegram_id, TaskStates.WAITING_CUSTOM_DEADLINE, data={"task_id": task.id})
        bot.edit_message_text(
            "Sanani DD.MM.YYYY HH:MM formatida yozib yuboring (masalan: 25.12.2026 18:30):",
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            reply_markup=cancel_kb(),
        )
        return

    now = timezone.localtime()
    if choice == "today":
        task.deadline = now.replace(hour=23, minute=59, second=0, microsecond=0)
    elif choice == "tomorrow":
        task.deadline = now.replace(hour=23, minute=59, second=0, microsecond=0) + timedelta(days=1)
    elif choice == "3d":
        task.deadline = now.replace(hour=23, minute=59, second=0, microsecond=0) + timedelta(days=3)
    task.save(update_fields=["deadline"])

    bot.answer_callback_query(call.id, "Deadline saqlandi ✅")
    handle_task_view(bot, call, user, ParsedCallback("task", "view", [task.id]))


def handle_custom_deadline_input(bot, message, user, state_data, clear_state):
    task_id = state_data.get("task_id")
    task = Task.objects.filter(id=task_id, user=user).first()
    clear_state(user.telegram_id)
    if not task:
        bot.send_message(message.chat.id, "Vazifa topilmadi.")
        return
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        task.deadline = timezone.make_aware(dt)
        task.save(update_fields=["deadline"])
        bot.send_message(message.chat.id, f"✅ Deadline saqlandi: {task.deadline.strftime('%d.%m.%Y %H:%M')}")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Format noto'g'ri. Namuna: 25.12.2026 18:30. Qaytadan urinib ko'ring (task detalidan qayta boshlang).")


# ---------------------------------------------------------------------------
# Tahrirlash
# ---------------------------------------------------------------------------

def handle_task_edit_menu(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    bot.edit_message_text(
        f"✏️ '{task.title}' — nimani tahrirlaymiz?",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=task_edit_menu_kb(task.id),
    )


def handle_edit_title_start(bot, call, user, cb: ParsedCallback, set_state):
    task_id = cb.param(0, int)
    set_state(user.telegram_id, TaskStates.WAITING_EDIT_TITLE, data={"task_id": task_id})
    bot.edit_message_text(
        "Yangi nomni kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_edit_title_input(bot, message, user, state_data, clear_state):
    task_id = state_data.get("task_id")
    task = Task.objects.filter(id=task_id, user=user).first()
    clear_state(user.telegram_id)
    if not task:
        bot.send_message(message.chat.id, "Vazifa topilmadi.")
        return
    task.title = message.text.strip()[:200]
    task.save(update_fields=["title"])
    bot.send_message(message.chat.id, f"✅ Nom yangilandi: {task.title}")


def handle_edit_desc_start(bot, call, user, cb: ParsedCallback, set_state):
    task_id = cb.param(0, int)
    set_state(user.telegram_id, TaskStates.WAITING_EDIT_DESC, data={"task_id": task_id})
    bot.edit_message_text(
        "Yangi tavsifni kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_edit_desc_input(bot, message, user, state_data, clear_state):
    task_id = state_data.get("task_id")
    task = Task.objects.filter(id=task_id, user=user).first()
    clear_state(user.telegram_id)
    if not task:
        bot.send_message(message.chat.id, "Vazifa topilmadi.")
        return
    task.description = message.text.strip()[:2000]
    task.save(update_fields=["description"])
    bot.send_message(message.chat.id, "✅ Tavsif yangilandi.")


def handle_edit_priority_start(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    bot.edit_message_text(
        "Yangi prioritetni tanlang:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=priority_pick_kb(task_id),
    )


def handle_edit_deadline_start(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    bot.edit_message_text(
        "Yangi deadline tanlang:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=deadline_quick_pick_kb(task_id),
    )


# ---------------------------------------------------------------------------
# O'chirish
# ---------------------------------------------------------------------------

def handle_task_delete_confirm(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    bot.edit_message_text(
        f"🗑 '{task.title}'ni rostdan o'chirmoqchimisiz?",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=task_delete_confirm_kb(task.id),
    )


def handle_task_delete(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    title = task.title
    task.delete()
    bot.answer_callback_query(call.id, "🗑 O'chirildi.")
    bot.edit_message_text(
        f"'{title}' o'chirildi.",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=tasks_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Subtasklar
# ---------------------------------------------------------------------------

def handle_subtasks_view(bot, call, user, cb: ParsedCallback):
    task_id = cb.param(0, int)
    task = Task.objects.filter(id=task_id, user=user).first()
    if not task:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    done, total = task.subtasks_progress
    text = f"☑️ Subtasklar ({progress_bar(done, total)}):" if total else "Hali subtask yo'q."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=subtasks_kb(task),
    )


def handle_toggle_subtask(bot, call, user, cb: ParsedCallback):
    subtask_id = cb.param(0, int)
    subtask = SubTask.objects.filter(id=subtask_id, task__user=user).select_related("task").first()
    if not subtask:
        bot.answer_callback_query(call.id, "Subtask topilmadi.", show_alert=True)
        return
    subtask.is_done = not subtask.is_done
    subtask.save(update_fields=["is_done"])
    handle_subtasks_view(bot, call, user, ParsedCallback("task", "subtasks", [subtask.task_id]))


def handle_add_subtask_start(bot, call, user, cb: ParsedCallback, set_state):
    task_id = cb.param(0, int)
    set_state(user.telegram_id, TaskStates.WAITING_SUBTASK_TITLE, data={"task_id": task_id})
    bot.edit_message_text(
        "Subtask nomini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_subtask_title_input(bot, message, user, state_data, clear_state):
    task_id = state_data.get("task_id")
    task = Task.objects.filter(id=task_id, user=user).first()
    clear_state(user.telegram_id)
    if not task:
        bot.send_message(message.chat.id, "Vazifa topilmadi.")
        return
    order = task.subtasks.count()
    SubTask.objects.create(task=task, title=message.text.strip()[:200], order=order)
    bot.send_message(message.chat.id, "✅ Subtask qo'shildi.")


# ---------------------------------------------------------------------------
# Kategoriyalar
# ---------------------------------------------------------------------------

def handle_categories_menu(bot, call, user):
    categories = Category.objects.filter(user=user)
    text = "📁 Kategoriyalar:" if categories else "Hali kategoriya yo'q."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=categories_kb(categories),
    )


def handle_create_category_start(bot, call, user, set_state):
    set_state(user.telegram_id, TaskStates.WAITING_CATEGORY_NAME, data={})
    bot.edit_message_text(
        "Kategoriya nomini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_category_name_input(bot, message, user, state_data, clear_state):
    name = message.text.strip()[:50]
    clear_state(user.telegram_id)
    if not name:
        bot.send_message(message.chat.id, "Nom bo'sh bo'lishi mumkin emas.")
        return
    category, created = Category.objects.get_or_create(user=user, name=name)
    if created:
        bot.send_message(message.chat.id, f"✅ '{category.name}' kategoriyasi yaratildi.")
    else:
        bot.send_message(message.chat.id, "Bu kategoriya allaqachon mavjud.")


def handle_list_by_category(bot, call, user, cb: ParsedCallback):
    category_id = cb.param(0, int)
    page = cb.param(1, int, 0)
    _render_task_list(
        bot, call.message.chat.id, call.message.message_id, user, page,
        category_id=category_id, back_target="task:categories",
    )


# ---------------------------------------------------------------------------
# Qidiruv
# ---------------------------------------------------------------------------

def handle_search_start(bot, call, user, set_state):
    set_state(user.telegram_id, TaskStates.WAITING_SEARCH_QUERY, data={})
    bot.edit_message_text(
        "Qidiruv so'zini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_search_query_input(bot, message, user, state_data, clear_state):
    query = message.text.strip()
    clear_state(user.telegram_id)
    if not query:
        bot.send_message(message.chat.id, "Qidiruv so'zi bo'sh bo'lishi mumkin emas.")
        return
    results = Task.objects.filter(user=user, title__icontains=query)[:15]
    if not results:
        bot.send_message(message.chat.id, f"'{query}' bo'yicha hech narsa topilmadi.")
        return
    text = "\n".join(format_task_line(t) for t in results)
    bot.send_message(message.chat.id, f"🔍 Natijalar:\n\n{text}")
