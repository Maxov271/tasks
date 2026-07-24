"""Focus/Pomodoro bo'limi — PomodoroSession modeli asosida."""
from django.utils import timezone

from apps.tasks.models import PomodoroSession
from services.xp_service import add_xp, XP_RULES
from bot.keyboards.focus_kb import focus_menu_kb, focus_active_kb
from bot.utils.callback_parser import ParsedCallback


def handle_focus_menu(bot, call, user):
    bot.edit_message_text(
        "🎯 Focus Mode. Necha daqiqalik sessiya boshlaymiz?",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_menu_kb(),
    )


def handle_focus_start(bot, call, user, cb: ParsedCallback):
    minutes = cb.param(0, int, 25)
    session = PomodoroSession.objects.create(user=user, duration_minutes=minutes)
    bot.answer_callback_query(call.id, f"{minutes} daqiqalik fokus sessiyasi boshlandi 🎯")
    bot.edit_message_text(
        f"⏳ {minutes} daqiqa davom etadi. Tugagach '⏸ To'xtatish' orqali yakunlang. Omad!",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_active_kb(session_id=session.id),
    )


def handle_focus_stop(bot, call, user, cb: ParsedCallback):
    session_id = cb.param(0, int)
    session = PomodoroSession.objects.filter(id=session_id, user=user).first()
    if not session:
        bot.answer_callback_query(call.id, "Sessiya topilmadi.", show_alert=True)
        return
    if session.stopped_at:
        bot.answer_callback_query(call.id, "Bu sessiya allaqachon yakunlangan.")
        return

    session.stopped_at = timezone.now()
    elapsed_minutes = (session.stopped_at - session.started_at).total_seconds() / 60
    session.is_completed = elapsed_minutes >= session.duration_minutes * 0.9  # 90%+ bajarilsa "to'liq" hisoblanadi
    session.save(update_fields=["stopped_at", "is_completed"])

    if session.is_completed:
        add_xp(user, XP_RULES["pomodoro_session"], reason="pomodoro_session")
        xp_note = f" +{XP_RULES['pomodoro_session']} XP 🎉"
    else:
        xp_note = " (to'liq bajarilmadi, XP berilmadi)"

    bot.edit_message_text(
        f"⏹ Sessiya yakunlandi: {int(elapsed_minutes)} daqiqa.{xp_note}",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_menu_kb(),
    )


def handle_focus_today_stats(bot, call, user):
    today = timezone.localdate()
    sessions = PomodoroSession.objects.filter(user=user, started_at__date=today, is_completed=True)
    total_minutes = sum(s.duration_minutes for s in sessions)
    text = f"📊 Bugungi fokus: {sessions.count()} ta sessiya, jami {total_minutes} daqiqa."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_menu_kb(),
    )


def handle_focus_weekly_report(bot, call, user):
    week_ago = timezone.now() - timezone.timedelta(days=7)
    sessions = PomodoroSession.objects.filter(user=user, started_at__gte=week_ago, is_completed=True)
    total_minutes = sum(s.duration_minutes for s in sessions)
    text = f"📅 Oxirgi 7 kun: {sessions.count()} ta sessiya, jami {total_minutes} daqiqa ({total_minutes // 60} soat)."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_menu_kb(),
    )
