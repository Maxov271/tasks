from django.db import models
from django.utils import timezone


class XPTransaction(models.Model):
    """Har bir XP o'zgarishi audit uchun alohida yoziladi — UserLevel esa
    tez o'qish uchun denormalized jami qiymatni saqlaydi."""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="xp_transactions")
    amount = models.IntegerField()
    reason = models.CharField(max_length=100)  # "task_done", "streak_bonus", "homework_submitted"...
    group = models.ForeignKey("groups.Group", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.amount:+d} ({self.reason})"


class UserLevel(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="level_info")
    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: Lv.{self.level} ({self.total_xp} XP)"


class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True)  # "100_tasks", "30_day_streak"
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon_emoji = models.CharField(max_length=10, default="🏅")

    def __str__(self):
        return self.title


class UserBadge(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="earned_by")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "badge")

    def __str__(self):
        return f"{self.user} earned {self.badge}"


class Streak(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="streak")
    current_daily = models.PositiveSmallIntegerField(default=0)
    longest_daily = models.PositiveSmallIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    freeze_available = models.BooleanField(default=True, help_text="Oyiga 1 marta streakni saqlab qolish imkoniyati")
    freeze_used_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user}: {self.current_daily} kunlik streak"

    def register_activity(self, today=None):
        """Bugungi faollikni belgilaydi va streakni yangilaydi.
        Chaqiruvchi (services/xp_service.py) bu metodni har faol amalda chaqiradi,
        lekin bir kunda faqat bir marta hisoblanishini o'zi nazorat qiladi."""
        today = today or timezone.localdate()
        if self.last_active_date == today:
            return  # bugun allaqachon hisoblangan
        yesterday = today - timezone.timedelta(days=1)
        if self.last_active_date == yesterday:
            self.current_daily += 1
        elif self.last_active_date and self.freeze_available and self.last_active_date == yesterday - timezone.timedelta(days=1):
            # streak freeze — bir kun o'tkazib yuborilgan bo'lsa ham davom ettiriladi
            self.current_daily += 1
            self.freeze_available = False
            self.freeze_used_at = today
        else:
            self.current_daily = 1
        self.longest_daily = max(self.longest_daily, self.current_daily)
        self.last_active_date = today
        self.save()
