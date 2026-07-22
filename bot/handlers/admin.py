"""
Bot ichidagi tezkor Admin Panel (Django Admin'ga qo'shimcha — mobil orqali
tezkor ban/statistika ko'rish uchun). Har bir funksiya @require_role bilan himoyalangan.
"""
from django.core.paginator import Paginator

from apps.users.models import User, Role
from apps.core.models import AdminActionLog
from bot.keyboards.admin_kb import admin_menu_kb, user_admin_actions_kb
from bot.middlewares.role_check import require_role
from bot.utils.callback_parser import ParsedCallback

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
    text = "\n".join(f"{'🚫' if u.is_banned else '✅'} {u.display_name} (id={u.id})" for u in page_obj.object_list)
    bot.edit_message_text(
        text or "Foydalanuvchi topilmadi.",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=admin_menu_kb(),
    )


@require_role(Role.ADMIN, Role.SUPER_ADMIN)
def handle_admin_ban(bot, call, user, cb: ParsedCallback):
    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    target.is_banned = True
    target.save(update_fields=["is_banned"])

    AdminActionLog.objects.create(
        actor_telegram_id=user.telegram_id, action="ban_user",
        target_model="User", target_id=target.id,
    )
    bot.answer_callback_query(call.id, f"{target.display_name} ban qilindi.")
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=user_admin_actions_kb(target.id),
    )


@require_role(Role.SUPER_ADMIN)
def handle_admin_assign_admin_role(bot, call, user, cb: ParsedCallback):
    """Faqat Super Admin boshqa foydalanuvchini Admin qila oladi."""
    from apps.users.models import UserRole

    target_id = cb.param(0, int)
    target = User.objects.filter(id=target_id).first()
    if not target:
        bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi.", show_alert=True)
        return
    role, _ = Role.objects.get_or_create(name=Role.ADMIN)
    UserRole.objects.get_or_create(user=target, role=role, group=None)

    AdminActionLog.objects.create(
        actor_telegram_id=user.telegram_id, action="assign_admin_role",
        target_model="User", target_id=target.id,
    )
    bot.answer_callback_query(call.id, f"{target.display_name} endi Admin.")
