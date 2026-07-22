"""Calendar bo'limi — Task va CalendarEvent deadline'larini birlashtirib ko'rsatadi."""
from collections import defaultdict
from django.utils import timezone

from apps.tasks.models import Task
from apps.calendar_app.models import CalendarEvent
from bot.keyboards.calendar_kb import calendar_month_kb
from bot.utils.callback_parser import ParsedCallback


def _days_with_events(user, year: int, month: int) -> dict:
    counts = defaultdict(int)
    for t in Task.objects.filter(user=user, deadline__year=year, deadline__month=month):
        counts[t.deadline.day] += 1
    for e in CalendarEvent.objects.filter(user=user, starts_at__year=year, starts_at__month=month):
        counts[e.starts_at.day] += 1
    return dict(counts)


def handle_calendar_menu(bot, call, user):
    now = timezone.localtime()
    handle_calendar_month(bot, call, user, ParsedCallback("calendar", "month", [now.year, now.month]))


def handle_calendar_month(bot, call, user, cb: ParsedCallback):
    year = cb.param(0, int)
    month = cb.param(1, int)
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    events = _days_with_events(user, year, month)
    bot.edit_message_text(
        "📅 Kalendar",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=calendar_month_kb(year, month, events),
    )
