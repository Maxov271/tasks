"""Habits bo'limi — to'liq: yaratish, belgilash, statistika, o'chirish."""
from django.utils import timezone

from apps.tasks.models import Habit, HabitLog
from services.xp_service import add_xp
from bot.keyboards.habits_kb import habits_menu_kb, habit_delete_list_kb
from bot.utils.callback_parser import ParsedCallback
from bot.utils.formatters import progress_bar
from bot.states.user_states import HabitStates


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
        text = "🔥 Odatlaringiz:\n\n" + "\n".join(lines)
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


def handle_habit_create_start(bot, call, user, set_state):
    set_state(user.telegram_id, HabitStates.WAITING_NAME, data={})
    bot.edit_message_text(
        "Yangi odat nomini kiriting (masalan: 'Kitob o'qish', 'Sport'):",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
    )


def handle_habit_name_input(bot, message, user, state_data, clear_state):
    name = message.text.strip()[:100]
    clear_state(user.telegram_id)
    if not name:
        bot.send_message(message.chat.id, "Nom bo'sh bo'lishi mumkin emas.")
        return
    Habit.objects.create(user=user, name=name)
    bot.send_message(message.chat.id, f"✅ '{name}' odati qo'shildi!")


def handle_habit_stats(bot, call, user):
    habits = Habit.objects.filter(user=user, is_active=True)
    if not habits:
        text = "Hali odat yo'q."
    else:
        lines = []
        last_30 = timezone.localdate() - timezone.timedelta(days=30)
        for h in habits:
            done_count = HabitLog.objects.filter(habit=h, date__gte=last_30, is_done=True).count()
            lines.append(f"{h.icon_emoji} {h.name}: {progress_bar(done_count, 30)}")
        text = "📈 Oxirgi 30 kunlik statistika:\n\n" + "\n".join(lines)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=habits_menu_kb(),
    )


def handle_habit_delete_list(bot, call, user):
    habits = Habit.objects.filter(user=user, is_active=True)
    text = "🗑 O'chirish uchun odatni tanlang:" if habits else "Hali odat yo'q."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=habit_delete_list_kb(habits),
    )


def handle_habit_delete(bot, call, user, cb: ParsedCallback):
    habit_id = cb.param(0, int)
    habit = Habit.objects.filter(id=habit_id, user=user).first()
    if not habit:
        bot.answer_callback_query(call.id, "Topilmadi.", show_alert=True)
        return
    habit.is_active = False
    habit.save(update_fields=["is_active"])
    bot.answer_callback_query(call.id, f"🗑 '{habit.name}' o'chirildi.")
    handle_habit_delete_list(bot, call, user)
