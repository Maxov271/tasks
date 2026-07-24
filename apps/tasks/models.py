from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Category(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#2ecc71", help_text="HEX rang, masalan #2ecc71")

    class Meta:
        unique_together = ("user", "name")
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Task(TimeStampedModel):
    """Shaxsiy vazifa."""

    LOW, MEDIUM, HIGH, URGENT = "low", "medium", "high", "urgent"
    PRIORITY_CHOICES = [(LOW, "Past"), (MEDIUM, "O'rta"), (HIGH, "Yuqori"), (URGENT, "Zudlik bilan")]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="tasks")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM)
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "is_done", "deadline"])]
        ordering = ["deadline", "-priority"]

    def __str__(self):
        return self.title

    def mark_done(self):
        self.is_done = True
        self.done_at = timezone.now()
        self.save(update_fields=["is_done", "done_at"])

    @property
    def is_overdue(self) -> bool:
        return bool(self.deadline and not self.is_done and self.deadline < timezone.now())

    @property
    def subtasks_progress(self):
        total = self.subtasks.count()
        done = self.subtasks.filter(is_done=True).count()
        return done, total


class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Reminder(models.Model):
    """Task/Habit/Deadline uchun umumiy eslatma. `content_type` + `object_id` orqali
    turli modellarga bog'lanadi (generic bog'lanish, contenttypes framework o'rniga
    soddalashtirilgan variant — kichik-o'rta loyiha uchun yetarli)."""

    TASK, HABIT, GROUP_TASK = "task", "habit", "group_task"
    TARGET_CHOICES = [(TASK, "Task"), (HABIT, "Habit"), (GROUP_TASK, "GroupTask")]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="reminders")
    target_type = models.CharField(max_length=12, choices=TARGET_CHOICES)
    target_id = models.PositiveIntegerField()
    remind_at = models.DateTimeField(db_index=True)
    is_sent = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["remind_at", "is_sent"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"Reminder for {self.target_type}#{self.target_id} @ {self.remind_at}"


# ---------------------------------------------------------------------------
# Guruh vazifalari
# ---------------------------------------------------------------------------

class GroupTask(TimeStampedModel):
    HOMEWORK, ASSIGNMENT, EXAM = "homework", "assignment", "exam"
    TYPE_CHOICES = [(HOMEWORK, "Uyga vazifa"), (ASSIGNMENT, "Kurs topshirig'i"), (EXAM, "Imtihon")]

    group = models.ForeignKey("groups.Group", on_delete=models.CASCADE, related_name="group_tasks")
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="created_group_tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=12, choices=TYPE_CHOICES, default=HOMEWORK)
    max_score = models.PositiveSmallIntegerField(default=100)
    deadline = models.DateTimeField(db_index=True)
    allow_late_submission = models.BooleanField(default=True)

    class Meta:
        ordering = ["-deadline"]

    def __str__(self):
        return f"{self.title} ({self.group})"


class TaskSubmission(TimeStampedModel):
    PENDING, GRADED, LATE = "pending", "graded", "late"
    STATUS_CHOICES = [(PENDING, "Kutilmoqda"), (GRADED, "Baholangan"), (LATE, "Kechikkan")]

    group_task = models.ForeignKey(GroupTask, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="submissions")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    mentor_comment = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="graded_submissions"
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("group_task", "user")

    def __str__(self):
        return f"{self.user} -> {self.group_task}"

    def save(self, *args, **kwargs):
        # Muddatdan keyin topshirilganini avtomatik belgilash
        if self.status == self.PENDING and self.group_task.deadline < timezone.now():
            self.status = self.LATE
        super().save(*args, **kwargs)


class TaskAttachment(models.Model):
    """
    Task, GroupTask yoki TaskSubmission'ga biriktirilgan fayl.
    `owner_type` + `owner_id` orqali soddalashtirilgan generic bog'lanish ishlatiladi.
    """
    TASK, GROUP_TASK, SUBMISSION = "task", "group_task", "submission"
    OWNER_CHOICES = [(TASK, "Task"), (GROUP_TASK, "GroupTask"), (SUBMISSION, "TaskSubmission")]

    ALLOWED_TYPES = ["pdf", "docx", "txt", "zip", "png", "jpg", "jpeg", "mp4", "mp3", "ogg", "text"]

    owner_type = models.CharField(max_length=12, choices=OWNER_CHOICES)
    owner_id = models.PositiveIntegerField()
    file_id = models.CharField(max_length=255, help_text="Telegram file_id")
    file_type = models.CharField(max_length=10, choices=[(t, t) for t in ALLOWED_TYPES])
    file_name = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="uploaded_attachments")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["owner_type", "owner_id"])]

    def __str__(self):
        return f"{self.file_name or self.file_id} ({self.owner_type}#{self.owner_id})"


# ---------------------------------------------------------------------------
# Habitlar
# ---------------------------------------------------------------------------

class Habit(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="habits")
    name = models.CharField(max_length=100)
    icon_emoji = models.CharField(max_length=10, default="✅")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    is_done = models.BooleanField(default=True)

    class Meta:
        unique_together = ("habit", "date")
        indexes = [models.Index(fields=["habit", "date"])]

    def __str__(self):
        return f"{self.habit} @ {self.date}"


# ---------------------------------------------------------------------------
# Focus / Pomodoro
# ---------------------------------------------------------------------------

class PomodoroSession(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="pomodoro_sessions")
    duration_minutes = models.PositiveSmallIntegerField(default=25)
    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False, help_text="To'liq davomida to'xtatilmagan bo'lsa True")

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["user", "started_at"])]

    def __str__(self):
        return f"{self.user}: {self.duration_minutes} daqiqa @ {self.started_at:%d.%m %H:%M}"
