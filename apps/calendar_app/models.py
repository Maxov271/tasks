from django.db import models


class CalendarEvent(models.Model):
    """
    Task/GroupTask deadline'laridan tashqari, foydalanuvchi qo'lda qo'shadigan
    custom hodisalar (dars, uchrashuv va h.k.) uchun. Kalendar bo'limida Task va
    GroupTask deadline'lari bilan birga (union query orqali) ko'rsatiladi.
    """
    EVENT, CLASS, MEETING = "event", "class", "meeting"
    TYPE_CHOICES = [(EVENT, "Hodisa"), (CLASS, "Dars"), (MEETING, "Uchrashuv")]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="calendar_events")
    group = models.ForeignKey("groups.Group", null=True, blank=True, on_delete=models.CASCADE, related_name="calendar_events")
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=EVENT)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["user", "starts_at"])]

    def __str__(self):
        return f"{self.title} @ {self.starts_at}"
