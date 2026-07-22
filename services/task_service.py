"""Shaxsiy va guruh vazifalari bilan bog'liq biznes-logika."""
from django.db import transaction
from django.utils import timezone

from apps.tasks.models import Task, TaskSubmission, GroupTask
from services.xp_service import add_xp, XP_RULES


@transaction.atomic
def complete_task(task: Task):
    """Taskni bajarilgan deb belgilaydi va XP beradi (muddatidan oldin bajarilsa bonus bilan)."""
    if task.is_done:
        return task
    task.mark_done()

    amount = XP_RULES["task_done"]
    if task.deadline and task.deadline >= timezone.now():
        amount += XP_RULES["task_done_on_time_bonus"]

    add_xp(task.user, amount, reason="task_done")
    return task


@transaction.atomic
def submit_group_task(group_task: GroupTask, user, attachment_file_ids=None):
    """Foydalanuvchi guruh vazifasini topshirganda chaqiriladi."""
    submission, created = TaskSubmission.objects.get_or_create(
        group_task=group_task, user=user
    )
    if not created and submission.status == TaskSubmission.GRADED:
        raise ValueError("Bu vazifa allaqachon baholangan, qayta topshirib bo'lmaydi.")

    submission.save()  # save() ichida late-status avtomatik hisoblanadi
    add_xp(user, XP_RULES["homework_submitted"], reason="homework_submitted", group=group_task.group)
    return submission


@transaction.atomic
def grade_submission(submission: TaskSubmission, score: int, mentor, comment: str = ""):
    if score < 0 or score > submission.group_task.max_score:
        raise ValueError(f"Ball 0 va {submission.group_task.max_score} orasida bo'lishi kerak.")
    submission.score = score
    submission.mentor_comment = comment
    submission.graded_by = mentor
    submission.graded_at = timezone.now()
    submission.status = TaskSubmission.GRADED
    submission.save()
    return submission
