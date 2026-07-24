"""
Calendar bo'limi — Task va CalendarEvent deadline'larini birlashtirib ko'rsatadi.
Kunlar holatga qarab ranglanadi (🔴 muddati o'tgan, 🟠 bugun, 🟡 kelgusi, 🟢 bajarilgan)
va kunni bosganda o'sha kundagi barcha vazifalar ro'yxati ochiladi.
"""
from collections import defaultdict
from django.utils import timezone

from apps.tasks.models import Task
from apps.calendar_app.models import CalendarEvent
from bot.keyboards.calendar_kb import calendar_month_kb, calendar_day_kb
from bot.utils.formatters import format_task_line
from bot.utils.callback_parser import ParsedCallback


def _day_status_map(user, year: int, month: int) -> dict:
    """Har bir kun uchun eng 'muhim' holatni aniqlaydi (rang tanlash uchun)."""
    today = timezone.localdate()
    day_tasks = defaultdict(list)

    for t in Task.objects.filter(user=user, deadline__year=year, deadline__month=month):
        day_tasks[t.deadline.day].append(t)
    for e in CalendarEvent.objects.filter(user=user, starts_at__year=year, starts_at__month=month):
        day_tasks[e.starts_at.day].append(e)

    status = {}
    for day, items in day_tasks.items():
        from datetime import date
        d = date(year, month, day)
        tasks_only = [i for i in items if hasattr(i, "is_done")]
        if tasks_only and all(t.is_done for t in tasks_only):
            status[day] = "done"
        elif d < today:
            status[day] = "overdue"
        elif d == today:
            status[day] = "today"
        else:
            status[day] = "upcoming"
    return status


def handle_calendar_menu(bot, call, user):
    now = timezone.localtime()
    handle_calendar_month(bot, call, user, ParsedCallback("calendar", "month", [now.year, now.month]))


def handle_calendar_today(bot, call, user):
    now = timezone.localtime()
    handle_calendar_day(bot, call, user, ParsedCallback("calendar", "day", [now.year, now.month, now.day]))


def handle_calendar_month(bot, call, user, cb: ParsedCallback):
    year = cb.param(0, int)
    month = cb.param(1, int)
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    status = _day_status_map(user, year, month)
    bot.edit_message_text(
        "📅 Kalendar\n\n🔴 muddati o'tgan · 🟠 bugun · 🟡 kelgusi · 🟢 bajarilgan",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=calendar_month_kb(year, month, status),
    )


def handle_calendar_day(bot, call, user, cb: ParsedCallback):
    """SO'RALGAN ASOSIY FUNKSIYA: sanani bossa o'sha kundagi vazifalar ro'yxati chiqadi."""
    year = cb.param(0, int)
    month = cb.param(1, int)
    day = cb.param(2, int)

    tasks = Task.objects.filter(user=user, deadline__year=year, deadline__month=month, deadline__day=day).order_by("deadline")
    events = CalendarEvent.objects.filter(user=user, starts_at__year=year, starts_at__month=month, starts_at__day=day)

    lines = [f"📅 {day:02d}.{month:02d}.{year}\n"]
    if not tasks and not events:
        lines.append("Bu kunga hech narsa rejalashtirilmagan.")
    else:
        if tasks:
            lines.append("📝 Vazifalar:")
            lines.extend(format_task_line(t) for t in tasks)
        if events:
            lines.append("\n🗓 Boshqa hodisalar:")
            lines.extend(f"• {e.title} ({e.starts_at.strftime('%H:%M')})" for e in events)

    bot.edit_message_text(
        "\n".join(lines), chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=calendar_day_kb(year, month, day),
    )


def handle_calendar_add_task_start(bot, call, user, cb: ParsedCallback, set_state):
    from bot.states.user_states import TaskStates

    year, month, day = cb.param(0, int), cb.param(1, int), cb.param(2, int)
    set_state(user.telegram_id, TaskStates.WAITING_TITLE, data={"prefill_deadline": f"{year}-{month}-{day}"})
    bot.edit_message_text(
        "Vazifa nomini kiriting (deadline avtomatik shu kunga o'rnatiladi):",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
    )
