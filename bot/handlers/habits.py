"""Habits bo'limi (qisqartirilgan, tasks.py naqshiga mos)."""
from django.utils import timezone

from apps.tasks.models import Habit, HabitLog
from services.xp_service import add_xp
from bot.keyboards.habits_kb import habits_menu_kb
from bot.utils.formatters import progress_bar


def handle_habits_menu(bot, call, user):
    habits = Habit.objects.filter(user=user, is_active=True)
    if not habits:
        text = "Sizda hali odat yo'q. ➕ orqali qo'shing."
    else:
        today = timezone.localdate()
        lines = []
        for h in habits:
            done_today = HabitLog.objects.filter(habit=h, date=today, is_done=True).exists()
            lines.append(f"{'✅' if done_today else '⬜️'} {h.icon_emoji} {h.name}")
        text = "\n".join(lines)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=habits_menu_kb(),
    )


def handle_check_today(bot, call, user):
    today = timezone.localdate()
    habits = Habit.objects.filter(user=user, is_active=True)
    created = 0
    for h in habits:
        _, was_created = HabitLog.objects.get_or_create(habit=h, date=today, defaults={"is_done": True})
        if was_created:
            created += 1
    if created:
        add_xp(user, created * 3, reason="habit_checked")
    bot.answer_callback_query(call.id, f"{created} ta odat bugungi kun uchun belgilandi ✅")
    handle_habits_menu(bot, call, user)
