"""
Ishlatish: python manage.py bootstrap_roles

Barcha 5 ta standart rolni (Super Admin, Admin, Mentor, Group Owner, User)
bazaga yaratadi (agar hali mavjud bo'lmasa). Loyihani birinchi marta
sozlaganda ishlatish tavsiya etiladi.
"""
from django.core.management.base import BaseCommand
from apps.users.models import Role


class Command(BaseCommand):
    help = "Standart rollarni (Super Admin, Admin, Mentor, Group Owner, User) bazaga yaratadi."

    def handle(self, *args, **options):
        created_count = 0
        for name, _ in Role.CHOICES:
            _, created = Role.objects.get_or_create(name=name)
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"✅ Tayyor. {created_count} ta yangi rol yaratildi (jami {len(Role.CHOICES)} ta)."))
