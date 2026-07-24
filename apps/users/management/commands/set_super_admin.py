"""
Ishlatish: python manage.py set_super_admin <telegram_id>

Foydalanuvchini (avval botga /start bergan bo'lishi kerak) global Super Admin
qilib tayinlaydi. Loyihani birinchi marta sozlashda o'zingizni admin qilish
uchun eng qulay usul — shell orqali qo'lda yozish shart emas.
"""
from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User, Role, UserRole


class Command(BaseCommand):
    help = "Berilgan telegram_id'ga ega foydalanuvchini Super Admin qiladi."

    def add_arguments(self, parser):
        parser.add_argument("telegram_id", type=int, help="Foydalanuvchining Telegram ID raqami")

    def handle(self, *args, **options):
        telegram_id = options["telegram_id"]
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise CommandError(
                f"telegram_id={telegram_id} bilan foydalanuvchi topilmadi. "
                "Avval shu foydalanuvchi botga /start yozgan bo'lishi kerak."
            )

        role, _ = Role.objects.get_or_create(name=Role.SUPER_ADMIN)
        _, created = UserRole.objects.get_or_create(user=user, role=role, group=None)

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ {user.display_name} (id={user.id}) endi Super Admin."))
        else:
            self.stdout.write(self.style.WARNING(f"{user.display_name} allaqachon Super Admin edi."))
