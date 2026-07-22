from django.db import models
from apps.core.models import TimeStampedModel


class User(TimeStampedModel):
    """Botdagi har bir foydalanuvchi. Django's built-in auth.User bilan aralashtirilmaydi —
    bu alohida, Telegram'ga xos model (admin panelga kirish kerak bo'lsa, alohida
    auth.User orqali staff account yaratiladi)."""

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=64, blank=True, null=True)
    full_name = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    language = models.CharField(max_length=5, default="uz", choices=[("uz", "O'zbek"), ("ru", "Русский"), ("en", "English")])

    is_premium = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.CharField(max_length=255, blank=True)
    can_create_group = models.BooleanField(default=False, help_text="Admin tomonidan beriladigan ruxsat")

    last_active_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_banned", "is_premium"]),
            models.Index(fields=["last_active_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} (@{self.username or '—'})"

    @property
    def display_name(self) -> str:
        return f"@{self.username}" if self.username else self.full_name


class Role(models.Model):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MENTOR = "mentor"
    GROUP_OWNER = "group_owner"
    USER = "user"

    CHOICES = [
        (SUPER_ADMIN, "Super Admin"),
        (ADMIN, "Admin"),
        (MENTOR, "Mentor"),
        (GROUP_OWNER, "Group Owner"),
        (USER, "User"),
    ]

    name = models.CharField(max_length=20, choices=CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class UserRole(TimeStampedModel):
    """
    User <-> Role bog'lanishi. `group` maydoni:
    - NULL bo'lsa -> global rol (masalan Super Admin, Admin)
    - to'ldirilgan bo'lsa -> faqat o'sha guruh doirasidagi rol (masalan Mentor, Group Owner)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_roles")
    group = models.ForeignKey(
        "groups.Group", null=True, blank=True, on_delete=models.CASCADE, related_name="role_assignments"
    )

    class Meta:
        unique_together = ("user", "role", "group")

    def __str__(self):
        scope = f" @ {self.group}" if self.group_id else " (global)"
        return f"{self.user} -> {self.role}{scope}"
