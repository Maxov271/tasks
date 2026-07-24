"""GroupTask (uyga vazifa/topshiriq/imtihon) yaratish, topshirish, baholash oqimi."""
from datetime import datetime

from django.core.paginator import Paginator
from django.utils import timezone

from apps.groups.models import Group
from apps.tasks.models import GroupTask, TaskSubmission, TaskAttachment
from services.task_service import submit_group_task, grade_submission
from bot.keyboards.group_tasks_kb import group_task_detail_kb, submissions_list_kb, gtask_type_pick_kb
from bot.keyboards.tasks_kb import cancel_kb
from bot.middlewares.role_check import user_has_group_role
from bot.utils.callback_parser import ParsedCallback
from bot.states.user_states import GroupTaskStates

PAGE_SIZE = 8


def _is_owner_or_mentor(user, group) -> bool:
    return group.owner_id == user.id or user_has_group_role(user, group, "mentor")


def handle_gtask_view(bot, call, user, cb: ParsedCallback):
    gtask_id = cb.param(0, int)
    gtask = GroupTask.objects.filter(id=gtask_id).select_related("group").first()
    if not gtask:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    submission = TaskSubmission.objects.filter(group_task=gtask, user=user).first()
    is_staff = _is_owner_or_mentor(user, gtask.group)

    lines = [f"📌 {gtask.title} ({gtask.get_task_type_display()})"]
    if gtask.description:
        lines.append(gtask.description)
    lines.append(f"⏰ Muddat: {gtask.deadline.strftime('%d.%m.%Y %H:%M')}")
    lines.append(f"Maksimal ball: {gtask.max_score}")
    if submission:
        status_label = {"pending": "🟡 Kutilmoqda", "graded": f"✅ Baholandi: {submission.score}/{gtask.max_score}", "late": "🔴 Kechikkan"}
        lines.append(f"Sizning holatingiz: {status_label.get(submission.status, submission.status)}")

    bot.edit_message_text(
        "\n".join(lines), chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_task_detail_kb(gtask, submission, is_staff),
    )


# --- Mentor: yaratish (FSM) ---

def handle_gtask_create_start(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group or not _is_owner_or_mentor(user, group):
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    bot.edit_message_text(
        "Vazifa turini tanlang:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=gtask_type_pick_kb(group_id),
    )


def handle_gtask_set_type(bot, call, user, cb: ParsedCallback, set_state):
    group_id = cb.param(0, int)
    task_type = cb.param(1, str)
    set_state(user.telegram_id, GroupTaskStates.WAITING_TITLE, data={"group_id": group_id, "task_type": task_type})
    bot.edit_message_text(
        "Vazifa nomini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_gtask_title_input(bot, message, user, state_data, set_state):
    title = message.text.strip()[:200]
    data = dict(state_data)
    data["title"] = title
    set_state(user.telegram_id, GroupTaskStates.WAITING_DEADLINE, data=data)
    bot.send_message(message.chat.id, "Muddatni DD.MM.YYYY HH:MM formatida kiriting (masalan 30.12.2026 23:59):")


def handle_gtask_deadline_input(bot, message, user, state_data, clear_state):
    group_id = state_data.get("group_id")
    group = Group.objects.filter(id=group_id).first()
    if not group or not _is_owner_or_mentor(user, group):
        clear_state(user.telegram_id)
        bot.send_message(message.chat.id, "Ruxsat yo'q.")
        return
    try:
        dt = timezone.make_aware(datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M"))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Format noto'g'ri. Namuna: 30.12.2026 23:59. Qaytadan kiriting:")
        return

    gtask = GroupTask.objects.create(
        group=group, created_by=user, title=state_data.get("title", "Nomsiz vazifa"),
        task_type=state_data.get("task_type", GroupTask.HOMEWORK), deadline=dt,
    )
    clear_state(user.telegram_id)

    from apps.groups.models import GroupMembership
    from apps.notifications.models import Notification
    from services.notification_service import enqueue_notification

    members = GroupMembership.objects.filter(group=group, is_active=True, role_in_group=GroupMembership.STUDENT)
    for m in members:
        enqueue_notification(
            m.user, Notification.HOMEWORK,
            f"📚 Yangi vazifa: '{gtask.title}' ({group.name}). Muddat: {dt.strftime('%d.%m.%Y %H:%M')}",
            scheduled_for=timezone.now(),
        )
    bot.send_message(message.chat.id, f"✅ '{gtask.title}' vazifasi yaratildi va {members.count()} a'zoga xabar berildi.")


# --- Student: topshirish ---

def handle_gtask_submit_start(bot, call, user, cb: ParsedCallback, set_state):
    gtask_id = cb.param(0, int)
    gtask = GroupTask.objects.filter(id=gtask_id).first()
    if not gtask:
        bot.answer_callback_query(call.id, "Vazifa topilmadi.", show_alert=True)
        return
    set_state(user.telegram_id, GroupTaskStates.WAITING_SUBMISSION_FILE, data={"gtask_id": gtask_id})
    bot.edit_message_text(
        f"'{gtask.title}' uchun faylingizni yuboring (pdf/docx/txt/zip/rasm/video/audio) "
        f"yoki matn ko'rinishida javob yozing:",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def _detect_file_type(document_or_photo, message) -> str:
    if message.content_type == "document":
        name = (document_or_photo.file_name or "").lower()
        for ext in TaskAttachment.ALLOWED_TYPES:
            if name.endswith(f".{ext}"):
                return ext
        return "zip"  # noma'lum kengaytma uchun fallback
    if message.content_type == "photo":
        return "jpg"
    if message.content_type == "video":
        return "mp4"
    if message.content_type in ("audio", "voice"):
        return "mp3"
    return "text"


def handle_gtask_submission_file(bot, message, user, state_data, clear_state):
    gtask_id = state_data.get("gtask_id")
    gtask = GroupTask.objects.filter(id=gtask_id).first()
    if not gtask:
        clear_state(user.telegram_id)
        bot.send_message(message.chat.id, "Vazifa topilmadi.")
        return

    try:
        submission = submit_group_task(gtask, user)
    except ValueError as e:
        clear_state(user.telegram_id)
        bot.send_message(message.chat.id, f"❌ {e}")
        return

    file_id = None
    file_type = "text"
    file_name = ""
    if message.content_type == "document":
        file_id = message.document.file_id
        file_type = _detect_file_type(message.document, message)
        file_name = message.document.file_name or ""
    elif message.content_type == "photo":
        file_id = message.photo[-1].file_id
        file_type = "jpg"
    elif message.content_type == "video":
        file_id = message.video.file_id
        file_type = "mp4"
    elif message.content_type in ("audio", "voice"):
        file_id = (message.audio or message.voice).file_id
        file_type = "mp3"

    if file_id:
        TaskAttachment.objects.create(
            owner_type=TaskAttachment.SUBMISSION, owner_id=submission.id,
            file_id=file_id, file_type=file_type, file_name=file_name, uploaded_by=user,
        )

    clear_state(user.telegram_id)
    status_note = " (⚠️ muddatdan kech topshirildi)" if submission.status == TaskSubmission.LATE else ""
    bot.send_message(message.chat.id, f"✅ '{gtask.title}' topshirildi{status_note}. XP qo'shildi!")


# --- Mentor: baholash ---

def handle_gtask_submissions_list(bot, call, user, cb: ParsedCallback):
    gtask_id = cb.param(0, int)
    page = cb.param(1, int, 0)
    gtask = GroupTask.objects.filter(id=gtask_id).select_related("group").first()
    if not gtask or not _is_owner_or_mentor(user, gtask.group):
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    qs = TaskSubmission.objects.filter(group_task=gtask).select_related("user")
    page_obj = Paginator(qs, PAGE_SIZE).get_page(page + 1)
    text = "📥 Topshirilganlar:" if page_obj.object_list else "Hali hech kim topshirmagan."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=submissions_list_kb(gtask.id, page_obj.object_list, page, page_obj.has_next()),
    )


def handle_gtask_grade_start(bot, call, user, cb: ParsedCallback, set_state):
    submission_id = cb.param(0, int)
    submission = TaskSubmission.objects.filter(id=submission_id).select_related("group_task__group").first()
    if not submission or not _is_owner_or_mentor(user, submission.group_task.group):
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    set_state(user.telegram_id, GroupTaskStates.WAITING_GRADE_SCORE, data={"submission_id": submission_id})
    bot.edit_message_text(
        f"{submission.user.display_name} uchun ball kiriting (0-{submission.group_task.max_score}):",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=cancel_kb(),
    )


def handle_gtask_grade_score_input(bot, message, user, state_data, set_state):
    submission_id = state_data.get("submission_id")
    submission = TaskSubmission.objects.filter(id=submission_id).select_related("group_task").first()
    if not submission:
        bot.send_message(message.chat.id, "Topilmadi.")
        return
    try:
        score = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "Faqat son kiriting.")
        return

    data = dict(state_data)
    data["score"] = score
    set_state(user.telegram_id, GroupTaskStates.WAITING_GRADE_COMMENT, data=data)
    bot.send_message(message.chat.id, "Izoh yozing (yoki '-' agar bo'lmasa):")


def handle_gtask_grade_comment_input(bot, message, user, state_data, clear_state):
    submission_id = state_data.get("submission_id")
    score = state_data.get("score")
    submission = TaskSubmission.objects.filter(id=submission_id).select_related("group_task").first()
    clear_state(user.telegram_id)
    if not submission:
        bot.send_message(message.chat.id, "Topilmadi.")
        return
    comment = "" if message.text.strip() == "-" else message.text.strip()[:1000]
    try:
        grade_submission(submission, score, mentor=user, comment=comment)
    except ValueError as e:
        bot.send_message(message.chat.id, f"❌ {e}")
        return

    from apps.notifications.models import Notification
    from services.notification_service import enqueue_notification

    enqueue_notification(
        submission.user, Notification.SYSTEM,
        f"✅ '{submission.group_task.title}' bahoolandi: {score}/{submission.group_task.max_score}"
        + (f"\n💬 {comment}" if comment else ""),
        scheduled_for=timezone.now(),
    )
    bot.send_message(message.chat.id, "✅ Baholandi va foydalanuvchiga xabar yuborildi.")
