"""
Boshqa barcha app'lar meros oladigan umumiy abstract modellar.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """created_at / updated_at maydonlarini avtomatik qo'shadi."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Ma'lumotni bazadan butunlay o'chirmasdan, is_deleted=True qilib belgilash uchun.
    Bu audit va "xato bilan o'chirib qo'yish"ning oldini olishga yordam beradi.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


class AdminActionLog(TimeStampedModel):
    """
    Django Admin yoki bot admin panel orqali qilingan har bir muhim amalning logi.
    Kim, nima qildi, qaysi obyektga — doim izlanadigan bo'lishi uchun.
    """
    actor_telegram_id = models.BigIntegerField(help_text="Amalni bajargan adminning telegram_id'si")
    action = models.CharField(max_length=100)  # "ban_user", "assign_role", "delete_group"...
    target_model = models.CharField(max_length=50, blank=True)  # "User", "Group"...
    target_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["actor_telegram_id", "created_at"]),
            models.Index(fields=["target_model", "target_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor_telegram_id} -> {self.action} ({self.target_model}#{self.target_id})"


class BotSetting(models.Model):
    """Global bot sozlamalari uchun oddiy key-value jadval (Django Admin orqali tahrirlanadi)."""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return self.key
