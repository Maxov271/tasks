from django.db import models
from apps.core.models import TimeStampedModel
from apps.core.utils import generate_invite_code


class Group(TimeStampedModel):
    """Bitta guruh/kurs. Owner — uni yaratgan (yoki admin tomonidan tayinlangan) foydalanuvchi."""

    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    owner = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="owned_groups")
    invite_code = models.CharField(max_length=16, unique=True, db_index=True, editable=False)
    is_active = models.BooleanField(default=True)
    max_members = models.PositiveIntegerField(null=True, blank=True, help_text="Bo'sh bo'lsa, cheksiz")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.invite_code:
            code = generate_invite_code()
            while Group.objects.filter(invite_code=code).exists():
                code = generate_invite_code()
            self.invite_code = code
        super().save(*args, **kwargs)

    @property
    def active_members_count(self) -> int:
        return self.members.filter(is_active=True).count()


class GroupMembership(TimeStampedModel):
    STUDENT = "student"
    MENTOR = "mentor"
    ROLE_CHOICES = [(STUDENT, "Student"), (MENTOR, "Mentor")]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    role_in_group = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "group")
        indexes = [models.Index(fields=["group", "is_active"])]

    def __str__(self):
        return f"{self.user} in {self.group} ({self.role_in_group})"


class Announcement(TimeStampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="announcements")
    author = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    is_sent = models.BooleanField(default=False, help_text="Barcha a'zolarga yuborilganini bildiradi")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.group}: {self.text[:40]}"
