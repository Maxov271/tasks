"""
/start va Dashboard bo'limi. Bu bot ichidagi "bosh sahifa" — hamma joydan
"⬅️ Orqaga" orqali shu yerga qaytiladi.
"""
from apps.users.models import User
from bot.keyboards.dashboard_kb import main_dashboard_kb
from bot.middlewares.role_check import user_has_role
from apps.users.models import Role


def get_or_create_user(telegram_user) -> User:
    user, created = User.objects.get_or_create(
        telegram_id=telegram_user.id,
        defaults={
            "username": telegram_user.username,
            "full_name": telegram_user.full_name or telegram_user.first_name,
        },
    )
    if not created:
        # Har safar profil ma'lumotlari o'zgargan bo'lishi mumkin (username almashtirish va h.k.)
        updated = False
        if user.username != telegram_user.username:
            user.username = telegram_user.username
            updated = True
        if updated:
            user.save(update_fields=["username"])
    return user


def render_dashboard_text(user: User) -> str:
    level_info = getattr(user, "level_info", None)
    xp_line = f"🏆 Level {level_info.level} · {level_info.total_xp} XP" if level_info else "🏆 Level 1 · 0 XP"
    return (
        f"👋 Xush kelibsiz, {user.display_name}!\n\n"
        f"{xp_line}\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )


def handle_start(bot, message):
    user = get_or_create_user(message.from_user)
    if user.is_banned:
        bot.send_message(message.chat.id, "🚫 Siz bloklangansiz. Savol bo'lsa, admin bilan bog'laning.")
        return

    is_admin = user_has_role(user, Role.ADMIN, Role.SUPER_ADMIN)
    is_mentor_owner = user_has_role(user, Role.MENTOR, Role.GROUP_OWNER)

    bot.send_message(
        message.chat.id,
        render_dashboard_text(user),
        reply_markup=main_dashboard_kb(is_admin=is_admin, is_mentor_or_owner=is_mentor_owner),
    )


def handle_dashboard_callback(bot, call, user):
    is_admin = user_has_role(user, Role.ADMIN, Role.SUPER_ADMIN)
    is_mentor_owner = user_has_role(user, Role.MENTOR, Role.GROUP_OWNER)
    bot.edit_message_text(
        render_dashboard_text(user),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=main_dashboard_kb(is_admin=is_admin, is_mentor_or_owner=is_mentor_owner),
    )
