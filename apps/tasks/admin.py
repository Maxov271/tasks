from django.contrib import admin
from .models import (
    Category, Task, SubTask, Reminder,
    GroupTask, TaskSubmission, TaskAttachment,
    Habit, HabitLog, PomodoroSession,
)


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "color")
    search_fields = ("name", "user__full_name")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "priority", "deadline", "is_done", "is_overdue")
    list_filter = ("priority", "is_done", "category")
    search_fields = ("title", "user__full_name")
    inlines = [SubTaskInline]

    @admin.display(boolean=True, description="Muddati o'tganmi")
    def is_overdue(self, obj):
        return obj.is_overdue


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "target_type", "target_id", "remind_at", "is_sent")
    list_filter = ("target_type", "is_sent")


class TaskSubmissionInline(admin.TabularInline):
    model = TaskSubmission
    extra = 0
    readonly_fields = ("user", "status", "created_at")


@admin.register(GroupTask)
class GroupTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "group", "task_type", "deadline", "max_score", "created_by")
    list_filter = ("task_type", "group")
    search_fields = ("title", "group__name")
    inlines = [TaskSubmissionInline]


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "group_task", "user", "status", "score", "graded_by", "graded_at")
    list_filter = ("status",)
    search_fields = ("user__full_name", "group_task__title")
    actions = ["mark_graded"]

    @admin.action(description="Tanlanganlarni 'baholangan' deb belgilash")
    def mark_graded(self, request, queryset):
        queryset.update(status=TaskSubmission.GRADED)


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "file_name", "file_type", "owner_type", "owner_id", "uploaded_by", "uploaded_at")
    list_filter = ("file_type", "owner_type")


class HabitLogInline(admin.TabularInline):
    model = HabitLog
    extra = 0


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "is_active")
    list_filter = ("is_active",)
    inlines = [HabitLogInline]


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ("id", "habit", "date", "is_done")
    list_filter = ("date",)


@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "duration_minutes", "started_at", "stopped_at", "is_completed")
    list_filter = ("is_completed",)
    search_fields = ("user__full_name",)
