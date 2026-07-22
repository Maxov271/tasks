"""Focus/Pomodoro bo'limi (skelet — real vaqt sanog'i Celery/background job orqali amalga oshadi)."""
from apps.tasks.models import Habit  # placeholder import chegara uchun emas — quyida PomodoroSession kerak bo'ladi
from bot.keyboards.focus_kb import focus_menu_kb, focus_active_kb
from bot.utils.callback_parser import ParsedCallback

# Eslatma: arxitektura hujjatida PomodoroSession modeli apps/tasks yoki alohida
# apps/focus ichida bo'lishi kerak — hozircha bu yerda referens sifatida qoldirildi,
# amalga oshirish bosqichida qo'shiladi.


def handle_focus_menu(bot, call, user):
    bot.edit_message_text(
        "🎯 Focus Mode. Necha daqiqalik sessiya boshlaymiz?",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_menu_kb(),
    )


def handle_focus_start(bot, call, user, cb: ParsedCallback):
    minutes = cb.param(0, int, 25)
    # TODO: PomodoroSession.objects.create(user=user, duration_minutes=minutes, started_at=now())
    bot.answer_callback_query(call.id, f"{minutes} daqiqalik fokus sessiyasi boshlandi 🎯")
    bot.edit_message_text(
        f"⏳ {minutes} daqiqa davom etadi. Omad!",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=focus_active_kb(session_id=0),
    )
