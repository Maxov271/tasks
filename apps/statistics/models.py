from django.db import models


class StatsSnapshot(models.Model):
    """
    Og'ir agregatsiyalar (jami/faol foydalanuvchilar, bugun bajarilgan tasklar va h.k.)
    har safar real-time hisoblanmaydi — Celery beat orqali soatlik/kunlik hisoblanib,
    shu jadvalga JSON sifatida yoziladi. Admin panel va bot shu snapshot'dan o'qiydi.
    """
    BOT, GROUP, USER = "bot", "group", "user"
    SCOPE_CHOICES = [(BOT, "Bot"), (GROUP, "Group"), (USER, "User")]

    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, db_index=True)
    scope_id = models.PositiveIntegerField(null=True, blank=True, help_text="Group/User ID, bot uchun NULL")
    period = models.CharField(max_length=10, default="daily")  # daily / weekly / monthly
    data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["scope", "scope_id", "period", "generated_at"])]
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.scope}#{self.scope_id or '-'} [{self.period}] @ {self.generated_at:%Y-%m-%d}"
