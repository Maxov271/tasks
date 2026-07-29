"""
Bildirishnoma servisi. IKKI xil rejim bor:

1. `send_now(bot, user, notification_type, text)` — DARHOL, sinxron yuboriladi
   (to'g'ridan-to'g'ri shu botning o'zi orqali). Guruh e'lonlari, vazifa haqida
   xabar berish, baholash natijasi, broadcast kabi FOYDALANUVCHI KUTAYOTGAN
   interaktiv amallar uchun ishlatiladi.

2. `enqueue_notification(user, ...)` — Notification jadvaliga 'pending' holatda
   yoziladi va uni FAQAT Celery worker (tasks_celery/reminders.py) keyinroq
   yuboradi. Bu FAQAT chindan ham kechiktirilishi kerak bo'lgan narsalar uchun
   ishlatiladi: deadline eslatmasi (ertaga), inactivity eslatmasi va h.k.

MUHIM: agar Celery worker (va Redis) ishga tushirilmagan bo'lsa,
`enqueue_notification` orqali yozilgan xabarlar HECH QACHON yuborilmaydi —
ular DB'da 'pending' holida qolib ketaveradi. Shu sababli interaktiv
funksiyalar (e'lon, broadcast, guruh vazifasi haqida xabar, baholash natijasi)
Celery'ga bog'liq bo'lmasligi uchun `send_now` orqali ishlaydi.
"""
from apps.notifications.models import Notification, NotificationPreference

# Har bir notification turi qaysi preference maydoniga mos kelishini bog'lash
TYPE_TO_PREF_FIELD = {
    Notification.DEADLINE: "deadline_reminders",
    Notification.HOMEWORK: "homework_reminders",
    Notification.INACTIVITY: "inactivity_reminders",
    Notification.STREAK: "streak_reminders",
    Notification.ANNOUNCEMENT: "announcements",
}


def _preference_allows(user, notification_type: str) -> bool:
    pref_field = TYPE_TO_PREF_FIELD.get(notification_type)
    if not pref_field:
        return True
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    return getattr(prefs, pref_field)


def send_now(bot, user, notification_type: str, text: str) -> bool:
    """
    Xabarni DARHOL, Celery'siz, to'g'ridan-to'g'ri shu bot orqali yuboradi.
    Natija DB'ga audit sifatida 'sent'/'failed' statusi bilan yoziladi (Notification
    jadvali statistika va tarix uchun ham ishlatiladi), lekin yuborish o'zi
    hech qanday fon vazifasiga bog'liq emas.

    Returns: True — muvaffaqiyatli yuborildi, False — o'chirilgan yoki xato.
    """
    from django.utils import timezone

    if not _preference_allows(user, notification_type):
        return False

    notification = Notification.objects.create(
        user=user, notification_type=notification_type, text=text,
        scheduled_for=timezone.now(),
    )
    try:
        bot.send_message(user.telegram_id, text)
        notification.status = Notification.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])
        return True
    except Exception as e:  # noqa: BLE001
        # Masalan foydalanuvchi botni bloklagan bo'lishi mumkin — bu kutilgan holat,
        # butun amalni (masalan e'lon yuborishni) to'xtatmasligi kerak.
        notification.status = Notification.FAILED
        notification.error_message = str(e)[:255]
        notification.save(update_fields=["status", "error_message"])
        return False


def send_now_bulk(bot, users, notification_type: str, text: str) -> dict:
    """Bir nechta foydalanuvchiga ketma-ket yuboradi (guruh e'loni, broadcast va h.k.).
    Telegram flood-control'ga tutilib qolmaslik uchun har bir yuborishdan keyin
    juda qisqa pauza qo'yiladi. Katta (1000+) auditoriya uchun buni Celery orqali
    partiyalarga bo'lib yuborish tavsiya etiladi — lekin kichik-o'rta guruh/bot
    uchun bu sinxron usul to'liq yetarli va Celery talab qilmaydi."""
    import time

    sent, failed, skipped = 0, 0, 0
    for u in users:
        if not _preference_allows(u, notification_type):
            skipped += 1
            continue
        ok = send_now(bot, u, notification_type, text)
        if ok:
            sent += 1
        else:
            failed += 1
        time.sleep(0.05)  # ~20 xabar/soniya — Telegram'ning umumiy limitidan xavfsiz pastda
    return {"sent": sent, "failed": failed, "skipped": skipped}


def enqueue_notification(user, notification_type: str, text: str, scheduled_for):
    """Kelajakda (Celery worker orqali) yuborilishi kerak bo'lgan xabarlar uchun —
    FAQAT haqiqatan kechiktirish kerak bo'lgan holatlarda ishlatiladi
    (deadline eslatmasi, inactivity eslatmasi, rejalashtirilgan hisobotlar)."""
    if not _preference_allows(user, notification_type):
        return None

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        text=text,
        scheduled_for=scheduled_for,
    )
