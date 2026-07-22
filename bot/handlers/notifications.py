"""Notifications bo'limi — foydalanuvchi sozlamalarini yoqib/o'chirish."""
from telebot import types

from apps.notifications.models import NotificationPreference
from bot.utils.callback_parser import build


PREF_LABELS = {
    "deadline_reminders": "⏰ Deadline eslatmalari",
    "homework_reminders": "📚 Uyga vazifa eslatmalari",
    "inactivity_reminders": "👋 Faolsizlik eslatmalari",
    "streak_reminders": "🔥 Streak eslatmalari",
    "daily_report": "📊 Kunlik hisobot",
    "weekly_report": "📈 Haftalik hisobot",
    "announcements": "📢 E'lonlar",
}


def notif_settings_kb(prefs: NotificationPreference) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for field, label in PREF_LABELS.items():
        state = "✅" if getattr(prefs, field) else "⬜️"
        kb.add(types.InlineKeyboardButton(f"{state} {label}", callback_data=build("notif", "toggle", field)))
    return kb


def handle_notif_menu(bot, call, user):
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    bot.edit_message_text(
        "🔔 Bildirishnoma sozlamalari — bosib yoqing/o'chiring:",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=notif_settings_kb(prefs),
    )


def handle_notif_toggle(bot, call, user, cb):
    field = cb.param(0, str)
    if field not in PREF_LABELS:
        bot.answer_callback_query(call.id, "Noma'lum sozlama.", show_alert=True)
        return
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    setattr(prefs, field, not getattr(prefs, field))
    prefs.save(update_fields=[field])
    handle_notif_menu(bot, call, user)
