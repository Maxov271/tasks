"""
Shaxsiy statistika bo'limi. Dashboard'dagi '📈 Statistics' tugmasi shu yerga
yo'naltiriladi (avvalgi versiyada bu domain butunlay unutilgan edi — endi tuzatildi).
"""
from django.utils import timezone

from telebot import types

from apps.tasks.models import Task, PomodoroSession
from apps.gamification.models import UserLevel, Streak
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def stats_menu_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(back_button("dashboard"))
    return kb


def handle_stats_menu(bot, call, user):
    total_tasks = Task.objects.filter(user=user).count()
    done_tasks = Task.objects.filter(user=user, is_done=True).count()
    completion_rate = round(100 * done_tasks / total_tasks) if total_tasks else 0

    level_info, _ = UserLevel.objects.get_or_create(user=user)
    streak, _ = Streak.objects.get_or_create(user=user)

    week_ago = timezone.now() - timezone.timedelta(days=7)
    pomodoro_minutes = sum(
        s.duration_minutes for s in PomodoroSession.objects.filter(user=user, started_at__gte=week_ago, is_completed=True)
    )

    text = (
        "📈 Shaxsiy statistika\n\n"
        f"✅ Bajarilgan vazifalar: {done_tasks}/{total_tasks} ({completion_rate}%)\n"
        f"🔥 Joriy streak: {streak.current_daily} kun\n"
        f"🏆 Level: {level_info.level} · {level_info.total_xp} XP\n"
        f"🎯 Oxirgi 7 kunlik fokus: {pomodoro_minutes} daqiqa"
    )
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=stats_menu_kb(),
    )
