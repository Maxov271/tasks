"""
Bot ichidagi tezkor Admin Panel. Har bir amal @require_role bilan himoyalangan
(faqat Admin/Super Admin). Broadcast va backup DARHOL bajariladi (Celery talab
qilinmaydi) — Celery mavjud bo'lsa backup fon vazifasi sifatida ham ishlaydi.
"""
from django.core.paginator import Paginator

from apps.users.models import User, Role
from apps.groups.models import Group
from apps.core.models import AdminActionLog
from apps.statistics.models import StatsSnapshot
from bot.keyboards.admin_kb import admin_menu_kb, admin_users_list_kb, user_admin_actions_kb, admin_groups_list_kb
from bot.keyboards.tasks_kb import cancel_kb
from bot.middlewares.role_check import require_role, user_has_role
from bot.utils.callback_parser import ParsedCallback
from bot.states.user_states import AdminStates

PAGE_SIZE = 10


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_menu(bot, call, user):
    bot.edit_message_text(
        "🛠 Admin Panel", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=admin_menu_kb(),
    )


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_users_list(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    qs = User.objects.order_by("-created_at")
    page_obj = Paginator(qs, PAGE_SIZE).get_page(page + 1)
    bot.edit_message_text(
        f"👤 Foydalanuvchilar ({qs.count()} ta):",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=admin_users_list_kb(page_obj.object_list, page, page_obj.has_next()),
    )


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_user_detail(bot, call, user, cb: ParsedCallback):
    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    text = (
        f"👤 {target.display_name} (id={target.id})\n"
        f"🚫 Ban: {'Ha' if target.is_banned else 'Yo\u02bbq'}\n"
        f"⭐ Premium: {'Ha' if target.is_premium else 'Yo\u02bbq'}\n"
        f"👥 Guruh yaratish ruxsati: {'Ha' if target.can_create_group else 'Yo\u02bbq'}"
    )
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=user_admin_actions_kb(target),
    )


def _log_and_reply(bot, call, user, target, action, refresh_cb):
    AdminActionLog.objects.create(
        actor_telegram_id=user.telegram_id, action=action, target_model="User", target_id=target.id,
    )
    handle_admin_user_detail(bot, call, user, refresh_cb)


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_ban(bot, call, user, cb: ParsedCallback):
    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    target.is_banned = True
    target.save(update_fields=["is_banned"])
    bot.answer_callback_query(call.id, f"{target.display_name} ban qilindi.")
    _log_and_reply(bot, call, user, target, "ban_user", cb)


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_unban(bot, call, user, cb: ParsedCallback):
    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    target.is_banned = False
    target.save(update_fields=["is_banned"])
    bot.answer_callback_query(call.id, f"{target.display_name} ban'dan chiqarildi.")
    _log_and_reply(bot, call, user, target, "unban_user", cb)


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_toggle_premium(bot, call, user, cb: ParsedCallback):
    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    target.is_premium = not target.is_premium
    target.save(update_fields=["is_premium"])
    bot.answer_callback_query(call.id, "⭐ Premium yangilandi.")
    _log_and_reply(bot, call, user, target, "toggle_premium", cb)


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_toggle_group_perm(bot, call, user, cb: ParsedCallback):
    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    target.can_create_group = not target.can_create_group
    target.save(update_fields=["can_create_group"])
    bot.answer_callback_query(call.id, "👥 Guruh yaratish ruxsati yangilandi.")
    _log_and_reply(bot, call, user, target, "toggle_group_permission", cb)


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_groups_list(bot, call, user, cb: ParsedCallback):
    page = cb.param(0, int, 0)
    qs = Group.objects.order_by("-created_at")
    page_obj = Paginator(qs, PAGE_SIZE).get_page(page + 1)
    bot.edit_message_text(
        f"👥 Guruhlar ({qs.count()} ta):",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=admin_groups_list_kb(page_obj.object_list, page, page_obj.has_next()),
    )


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_stats(bot, call, user):
    snapshot = StatsSnapshot.objects.filter(scope=StatsSnapshot.BOT).order_by("-generated_at").first()
    if not snapshot:
        text = (
            "📊 Hali statistika snapshoti yaratilmagan.\n"
            "Celery beat ishga tushgandan keyin har kuni avtomatik yaratiladi.\n"
            "Hozircha jonli sonlar:\n\n"
            f"👤 Jami userlar: {User.objects.count()}\n"
            f"👥 Jami guruhlar: {Group.objects.count()}"
        )
    else:
        d = snapshot.data
        text = (
            f"📊 Bot statistikasi ({snapshot.generated_at:%d.%m.%Y %H:%M}):\n\n"
            f"👤 Jami userlar: {d.get('total_users', '—')}\n"
            f"🆕 Bugun qo'shilgan: {d.get('new_today', '—')}\n"
            f"🟢 Bugun faol: {d.get('active_today', '—')}\n"
            f"✅ Bugun bajarilgan vazifalar: {d.get('tasks_done_today', '—')}\n"
            f"👥 Jami faol guruhlar: {d.get('total_groups', '—')}"
        )
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=admin_menu_kb(),
    )


@require_role(Role.SUPER_ADMIN)
def handle_admin_backup(bot, call, user):
    """
    Faqat Super Admin. Avval Celery orqali fon vazifasi sifatida yuborishga urinadi;
    agar Celery/Redis ishlamasa (odatiy holat — ko'pchilik kichik loyihalarda
    Celery alohida ishga tushirilmaydi), backup DARHOL, shu yerning o'zida
    sinxron bajariladi — foydalanuvchi "ishlamayapti" degan taassurotga
    tushmasligi uchun.
    """
    from tasks_celery.backups import run_daily_backup

    try:
        run_daily_backup.delay()
        text = "💾 Backup fon vazifasi navbatga qo'yildi (Celery worker orqali bajariladi)."
    except Exception:
        # Celery/Redis ishlamayapti — funksiyani oddiy Python funksiyasi sifatida,
        # hech qanday navbatsiz, to'g'ridan-to'g'ri shu yerda bajaramiz.
        try:
            run_daily_backup()  # Celery Task obyekti ham oddiy chaqiruvni qo'llab-quvvatlaydi
            text = "💾 Backup muvaffaqiyatli yaratildi (Celery ishlamagani uchun to'g'ridan-to'g'ri bajarildi)."
        except Exception as e:  # noqa: BLE001
            text = f"❌ Backup yaratishda xatolik: {e}"

    bot.answer_callback_query(call.id, "Backup so'rovi qayta ishlandi.")
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=admin_menu_kb(),
    )


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_broadcast_start(bot, call, user, set_state):
    set_state(user.telegram_id, AdminStates.WAITING_BROADCAST_TEXT, data={})
    bot.edit_message_text(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_admin_broadcast_text_input(bot, message, user, state_data, clear_state):
    if not user_has_role(user, Role.ADMIN, Role.SUPER_ADMIN):
        clear_state(user.telegram_id)
        bot.send_message(message.chat.id, "Ruxsat yo'q.")
        return

    text = message.text.strip()[:2000]
    clear_state(user.telegram_id)

    from apps.notifications.models import Notification
    from services.notification_service import send_now_bulk

    targets = list(User.objects.filter(is_banned=False))
    bot.send_message(message.chat.id, f"⏳ {len(targets)} foydalanuvchiga yuborilmoqda, biroz kuting...")

    result = send_now_bulk(bot, targets, Notification.SYSTEM, f"📢 {text}")

    AdminActionLog.objects.create(actor_telegram_id=user.telegram_id, action="broadcast", details={"text": text})
    bot.send_message(
        message.chat.id,
        f"✅ Broadcast yakunlandi: {result['sent']} ta yetdi"
        + (f", {result['failed']} tasiga yetmadi" if result['failed'] else "") + ".\n\n"
        "Eslatma: juda katta (minglab) foydalanuvchi bazasi uchun bu jarayon "
        "botni vaqtincha bandi qilishi mumkin — bunday holatda Celery-based "
        "partiyalash tavsiya etiladi.",
    )
