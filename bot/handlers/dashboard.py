"""
/start va Dashboard bo'limi. Bu bot ichidagi "bosh sahifa" — hamma joydan
"⬅️ Orqaga" orqali shu yerga qaytiladi.
"""
from apps.users.models import User
from bot.keyboards.dashboard_kb import main_dashboard_kb
from bot.middlewares.role_check import user_has_role
from apps.users.models import Role


def _build_full_name(telegram_user) -> str:
    """
    MUHIM TUZATISH: pyTelegramBotAPI'ning types.User klassida `full_name`
    atributi UMUMAN MAVJUD EMAS (bu faqat aiogram kutubxonasiga xos qulaylik).
    Avvalgi kodda `telegram_user.full_name` ishlatilgani sabab, bu funksiya
    chaqirilgan HAR BIR joyda (ya'ni deyarli har bir tugma va xabarda)
    AttributeError xatoligi yuzaga kelardi. Shu yerda first_name + last_name'dan
    qo'lda yig'ib olinadi.
    """
    first = getattr(telegram_user, "first_name", "") or ""
    last = getattr(telegram_user, "last_name", "") or ""
    full = f"{first} {last}".strip()
    return full or "Foydalanuvchi"


def get_or_create_user(telegram_user) -> User:
    user, created = User.objects.get_or_create(
        telegram_id=telegram_user.id,
        defaults={
            "username": telegram_user.username,
            "full_name": _build_full_name(telegram_user),
        },
    )
    if not created:
        # Har safar profil ma'lumotlari o'zgargan bo'lishi mumkin (username almashtirish va h.k.)
        updated_fields = []
        if user.username != telegram_user.username:
            user.username = telegram_user.username
            updated_fields.append("username")
        new_full_name = _build_full_name(telegram_user)
        if new_full_name != "Foydalanuvchi" and user.full_name != new_full_name:
            user.full_name = new_full_name
            updated_fields.append("full_name")
        if updated_fields:
            user.save(update_fields=updated_fields)
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

    # Eslatma: "🛠 Admin Panel" tugmasi faqat GLOBAL Admin/Super Admin uchun ko'rsatiladi.
    # Mentor/Group Owner o'z guruhini "Groups -> guruh -> ⚙️ Sozlamalar" orqali boshqaradi —
    # ular uchun bu tugmani ko'rsatish "ruxsat yo'q" xatosiga olib kelardi (tuzatildi).
    is_admin = user_has_role(user, Role.ADMIN, Role.SUPER_ADMIN)

    bot.send_message(
        message.chat.id,
        render_dashboard_text(user),
        reply_markup=main_dashboard_kb(is_admin=is_admin),
    )


def handle_dashboard_callback(bot, call, user):
    is_admin = user_has_role(user, Role.ADMIN, Role.SUPER_ADMIN)
    bot.edit_message_text(
        render_dashboard_text(user),
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=main_dashboard_kb(is_admin=is_admin),
    )
