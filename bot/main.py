"""
Bot ishga tushirish nuqtasi. Ishlatish:

    DJANGO_SETTINGS_MODULE=config.settings.dev python bot/main.py

Bu fayl Django'ni sozlaydi, telebot instance yaratadi va barcha callback_data'larni
domain bo'yicha tegishli handler'ga yo'naltiradi (markazlashgan dispatcher).
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
import telebot  # noqa: E402

from bot.handlers import (  # noqa: E402
    dashboard, tasks, groups, group_tasks, habits, focus, achievements,
    calendar as calendar_handlers, notifications, settings as settings_handlers,
    admin, stats,
)
from bot.middlewares.rate_limit import is_rate_limited  # noqa: E402
from bot.middlewares.logging_middleware import log_update, log_error  # noqa: E402
from bot.utils.callback_parser import parse, ParsedCallback  # noqa: E402

logger = logging.getLogger("bot")
bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")

# In-memory FSM holat saqlash (kichik loyiha uchun yetarli; katta yuklamada
# Redis-based storage'ga almashtiriladi — interfeys shu uchta funksiya orqali izolatsiya qilingan)
_user_states = {}


def set_state(telegram_id, state, data=None):
    _user_states[telegram_id] = {"state": state, "data": data or {}}


def get_state(telegram_id):
    return _user_states.get(telegram_id)


def clear_state(telegram_id):
    _user_states.pop(telegram_id, None)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["start"])
def on_start(message):
    log_update("message", message.from_user.id, "/start")
    dashboard.handle_start(bot, message)


# ---------------------------------------------------------------------------
# Callback query dispatcher — domain bo'yicha yo'naltirish
# ---------------------------------------------------------------------------

DOMAIN_HANDLERS = {
    "nav": {
        "open": lambda call, user, cb: dashboard.handle_dashboard_callback(bot, call, user),
    },
    "task": {
        "menu": lambda call, user, cb: tasks.handle_tasks_menu(bot, call, user),
        "list": lambda call, user, cb: tasks.handle_task_list(bot, call, user, cb),
        "list_done": lambda call, user, cb: tasks.handle_task_list_done(bot, call, user, cb),
        "list_upcoming": lambda call, user, cb: tasks.handle_task_list_upcoming(bot, call, user, cb),
        "view": lambda call, user, cb: tasks.handle_task_view(bot, call, user, cb),
        "done": lambda call, user, cb: tasks.handle_task_done(bot, call, user, cb),
        "create": lambda call, user, cb: tasks.handle_task_create_start(bot, call, user, set_state),
        "set_priority": lambda call, user, cb: tasks.handle_set_priority(bot, call, user, cb),
        "set_deadline": lambda call, user, cb: tasks.handle_set_deadline_quick(bot, call, user, cb, set_state),
        "edit": lambda call, user, cb: tasks.handle_task_edit_menu(bot, call, user, cb),
        "edit_title": lambda call, user, cb: tasks.handle_edit_title_start(bot, call, user, cb, set_state),
        "edit_desc": lambda call, user, cb: tasks.handle_edit_desc_start(bot, call, user, cb, set_state),
        "edit_priority": lambda call, user, cb: tasks.handle_edit_priority_start(bot, call, user, cb),
        "edit_deadline": lambda call, user, cb: tasks.handle_edit_deadline_start(bot, call, user, cb),
        "delete_confirm": lambda call, user, cb: tasks.handle_task_delete_confirm(bot, call, user, cb),
        "delete": lambda call, user, cb: tasks.handle_task_delete(bot, call, user, cb),
        "subtasks": lambda call, user, cb: tasks.handle_subtasks_view(bot, call, user, cb),
        "toggle_subtask": lambda call, user, cb: tasks.handle_toggle_subtask(bot, call, user, cb),
        "add_subtask": lambda call, user, cb: tasks.handle_add_subtask_start(bot, call, user, cb, set_state),
        "categories": lambda call, user, cb: tasks.handle_categories_menu(bot, call, user),
        "create_category": lambda call, user, cb: tasks.handle_create_category_start(bot, call, user, set_state),
        "list_by_category": lambda call, user, cb: tasks.handle_list_by_category(bot, call, user, cb),
        "search": lambda call, user, cb: tasks.handle_search_start(bot, call, user, set_state),
    },
    "group": {
        "menu": lambda call, user, cb: groups.handle_groups_menu(bot, call, user),
        "my_list": lambda call, user, cb: groups.handle_my_groups_list(bot, call, user),
        "view": lambda call, user, cb: groups.handle_group_detail(bot, call, user, cb),
        "create": lambda call, user, cb: groups.handle_group_create_start(bot, call, user, set_state),
        "join_by_code": lambda call, user, cb: groups.handle_join_by_code_start(bot, call, user, set_state),
        "tasks": lambda call, user, cb: groups.handle_group_tasks_list(bot, call, user, cb),
        "members": lambda call, user, cb: groups.handle_group_members_list(bot, call, user, cb),
        "member_actions": lambda call, user, cb: groups.handle_member_actions(bot, call, user, cb),
        "make_mentor": lambda call, user, cb: groups.handle_make_mentor(bot, call, user, cb),
        "make_student": lambda call, user, cb: groups.handle_make_student(bot, call, user, cb),
        "remove_member": lambda call, user, cb: groups.handle_remove_member(bot, call, user, cb),
        "leaderboard": lambda call, user, cb: groups.handle_group_leaderboard(bot, call, user, cb),
        "settings": lambda call, user, cb: groups.handle_group_settings(bot, call, user, cb),
        "rename": lambda call, user, cb: groups.handle_group_rename_start(bot, call, user, cb, set_state),
        "toggle_active": lambda call, user, cb: groups.handle_group_toggle_active(bot, call, user, cb),
        "announcements": lambda call, user, cb: groups.handle_announcements_list(bot, call, user, cb),
        "post_announcement": lambda call, user, cb: groups.handle_post_announcement_start(bot, call, user, cb, set_state),
    },
    "gtask": {
        "view": lambda call, user, cb: group_tasks.handle_gtask_view(bot, call, user, cb),
        "create": lambda call, user, cb: group_tasks.handle_gtask_create_start(bot, call, user, cb),
        "set_type": lambda call, user, cb: group_tasks.handle_gtask_set_type(bot, call, user, cb, set_state),
        "submit_start": lambda call, user, cb: group_tasks.handle_gtask_submit_start(bot, call, user, cb, set_state),
        "submissions": lambda call, user, cb: group_tasks.handle_gtask_submissions_list(bot, call, user, cb),
        "grade_start": lambda call, user, cb: group_tasks.handle_gtask_grade_start(bot, call, user, cb, set_state),
    },
    "habit": {
        "menu": lambda call, user, cb: habits.handle_habits_menu(bot, call, user),
        "check_today": lambda call, user, cb: habits.handle_check_today(bot, call, user),
        "create": lambda call, user, cb: habits.handle_habit_create_start(bot, call, user, set_state),
        "stats": lambda call, user, cb: habits.handle_habit_stats(bot, call, user),
        "delete_list": lambda call, user, cb: habits.handle_habit_delete_list(bot, call, user),
        "delete": lambda call, user, cb: habits.handle_habit_delete(bot, call, user, cb),
    },
    "focus": {
        "menu": lambda call, user, cb: focus.handle_focus_menu(bot, call, user),
        "start": lambda call, user, cb: focus.handle_focus_start(bot, call, user, cb),
        "stop": lambda call, user, cb: focus.handle_focus_stop(bot, call, user, cb),
        "today_stats": lambda call, user, cb: focus.handle_focus_today_stats(bot, call, user),
        "weekly_report": lambda call, user, cb: focus.handle_focus_weekly_report(bot, call, user),
    },
    "ach": {
        "menu": lambda call, user, cb: achievements.handle_achievements_menu(bot, call, user),
        "level_info": lambda call, user, cb: achievements.handle_level_info(bot, call, user),
        "my_badges": lambda call, user, cb: achievements.handle_my_badges(bot, call, user),
        "next_goal": lambda call, user, cb: achievements.handle_next_goal(bot, call, user),
        "leaderboard": lambda call, user, cb: achievements.handle_leaderboard(bot, call, user, cb),
    },
    "calendar": {
        "menu": lambda call, user, cb: calendar_handlers.handle_calendar_menu(bot, call, user),
        "today": lambda call, user, cb: calendar_handlers.handle_calendar_today(bot, call, user),
        "month": lambda call, user, cb: calendar_handlers.handle_calendar_month(bot, call, user, cb),
        "day": lambda call, user, cb: calendar_handlers.handle_calendar_day(bot, call, user, cb),
        "add_task": lambda call, user, cb: calendar_handlers.handle_calendar_add_task_start(bot, call, user, cb, set_state),
    },
    "notif": {
        "menu": lambda call, user, cb: notifications.handle_notif_menu(bot, call, user),
        "toggle": lambda call, user, cb: notifications.handle_notif_toggle(bot, call, user, cb),
    },
    "settings": {
        "menu": lambda call, user, cb: settings_handlers.handle_settings_menu(bot, call, user),
        "language": lambda call, user, cb: settings_handlers.handle_language_menu(bot, call, user),
        "set_language": lambda call, user, cb: settings_handlers.handle_set_language(bot, call, user, cb),
    },
    "profile": {
        "menu": lambda call, user, cb: settings_handlers.handle_profile_menu(bot, call, user),
    },
    "stats": {
        "menu": lambda call, user, cb: stats.handle_stats_menu(bot, call, user),
    },
    "admin": {
        "menu": lambda call, user, cb: admin.handle_admin_menu(bot, call, user),
        "users": lambda call, user, cb: admin.handle_admin_users_list(bot, call, user, cb),
        "user_detail": lambda call, user, cb: admin.handle_admin_user_detail(bot, call, user, cb),
        "ban": lambda call, user, cb: admin.handle_admin_ban(bot, call, user, cb),
        "unban": lambda call, user, cb: admin.handle_admin_unban(bot, call, user, cb),
        "toggle_premium": lambda call, user, cb: admin.handle_admin_toggle_premium(bot, call, user, cb),
        "toggle_group_perm": lambda call, user, cb: admin.handle_admin_toggle_group_perm(bot, call, user, cb),
        "groups": lambda call, user, cb: admin.handle_admin_groups_list(bot, call, user, cb),
        "stats": lambda call, user, cb: admin.handle_admin_stats(bot, call, user),
        "backup": lambda call, user, cb: admin.handle_admin_backup(bot, call, user),
        "broadcast": lambda call, user, cb: admin.handle_admin_broadcast_start(bot, call, user, set_state),
    },
}


def _dispatch(domain: str, action: str, params: list, call, user):
    """Berilgan domain/action/params bo'yicha DOMAIN_HANDLERS'dan mos funksiyani topib chaqiradi.
    `nav:back:<target>` kabi generic yo'naltirish uchun ham ishlatiladi."""
    domain_map = DOMAIN_HANDLERS.get(domain)
    action_func = domain_map.get(action) if domain_map else None
    if not action_func:
        return False
    cb = ParsedCallback(domain=domain, action=action, params=params)
    action_func(call, user, cb)
    return True


@bot.callback_query_handler(func=lambda call: call.data != "noop")
def on_callback(call):
    if is_rate_limited(call.from_user.id):
        bot.answer_callback_query(call.id, "⏳ Juda tez bosyapsiz, biroz kuting.")
        return

    log_update("callback", call.from_user.id, call.data)
    cb = parse(call.data)

    from bot.handlers.dashboard import get_or_create_user
    user = get_or_create_user(call.from_user)
    if user.is_banned:
        bot.answer_callback_query(call.id, "🚫 Siz bloklangansiz.", show_alert=True)
        return

    try:
        # "❌ Bekor qilish" — istalgan FSM holatini tozalab, dashboard'ga qaytaradi
        if cb.domain == "nav" and cb.action == "cancel":
            clear_state(call.from_user.id)
            dashboard.handle_dashboard_callback(bot, call, user)
            bot.answer_callback_query(call.id)
            return

        # "⬅️ Orqaga" — target ichiga kodlangan domain:action:params'ga qaytadi.
        # target "dashboard" bo'lsa yoki umuman topilmasa, bosh menyuga qaytariladi.
        if cb.domain == "nav" and cb.action == "back":
            target_parts = cb.params
            handled = False
            if target_parts and target_parts[0] != "dashboard":
                handled = _dispatch(target_parts[0], target_parts[1] if len(target_parts) > 1 else "menu", target_parts[2:], call, user)
            if not handled:
                dashboard.handle_dashboard_callback(bot, call, user)
            bot.answer_callback_query(call.id)
            return

        handled = _dispatch(cb.domain, cb.action, cb.params, call, user)
        if not handled:
            bot.answer_callback_query(call.id, "Bu bo'lim hali ishlab chiqilmoqda 🚧")
            return

        bot.answer_callback_query(call.id)
    except PermissionError as e:
        bot.answer_callback_query(call.id, str(e), show_alert=True)
    except Exception as e:  # noqa: BLE001
        log_error(call.from_user.id, e, context=call.data)
        bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi, qayta urinib ko'ring.")


# ---------------------------------------------------------------------------
# FSM matn kiritish handler'i
# ---------------------------------------------------------------------------

from bot.states.user_states import TaskStates, GroupStates, GroupTaskStates, HabitStates, AdminStates  # noqa: E402

TEXT_STATE_HANDLERS = {
    TaskStates.WAITING_TITLE: lambda message, user, data: tasks.handle_task_title_input(
        bot, message, user, data, set_state, clear_state),
    TaskStates.WAITING_CUSTOM_DEADLINE: lambda message, user, data: tasks.handle_custom_deadline_input(
        bot, message, user, data, clear_state),
    TaskStates.WAITING_EDIT_TITLE: lambda message, user, data: tasks.handle_edit_title_input(
        bot, message, user, data, clear_state),
    TaskStates.WAITING_EDIT_DESC: lambda message, user, data: tasks.handle_edit_desc_input(
        bot, message, user, data, clear_state),
    TaskStates.WAITING_SUBTASK_TITLE: lambda message, user, data: tasks.handle_subtask_title_input(
        bot, message, user, data, clear_state),
    TaskStates.WAITING_CATEGORY_NAME: lambda message, user, data: tasks.handle_category_name_input(
        bot, message, user, data, clear_state),
    TaskStates.WAITING_SEARCH_QUERY: lambda message, user, data: tasks.handle_search_query_input(
        bot, message, user, data, clear_state),

    GroupStates.WAITING_NAME: lambda message, user, data: (
        groups.handle_group_rename_input(bot, message, user, data, clear_state)
        if "rename_group_id" in data else
        groups.handle_group_name_input(bot, message, user, data, set_state)
    ),
    GroupStates.WAITING_DESCRIPTION: lambda message, user, data: groups.handle_group_description_input(
        bot, message, user, data, clear_state),
    GroupStates.WAITING_INVITE_CODE: lambda message, user, data: groups.handle_invite_code_input(
        bot, message, user, data, clear_state),
    GroupStates.WAITING_ANNOUNCEMENT_TEXT: lambda message, user, data: groups.handle_announcement_text_input(
        bot, message, user, data, clear_state),

    GroupTaskStates.WAITING_TITLE: lambda message, user, data: group_tasks.handle_gtask_title_input(
        bot, message, user, data, set_state),
    GroupTaskStates.WAITING_DEADLINE: lambda message, user, data: group_tasks.handle_gtask_deadline_input(
        bot, message, user, data, clear_state),
    GroupTaskStates.WAITING_GRADE_SCORE: lambda message, user, data: group_tasks.handle_gtask_grade_score_input(
        bot, message, user, data, set_state),
    GroupTaskStates.WAITING_GRADE_COMMENT: lambda message, user, data: group_tasks.handle_gtask_grade_comment_input(
        bot, message, user, data, clear_state),

    HabitStates.WAITING_NAME: lambda message, user, data: habits.handle_habit_name_input(
        bot, message, user, data, clear_state),

    AdminStates.WAITING_BROADCAST_TEXT: lambda message, user, data: admin.handle_admin_broadcast_text_input(
        bot, message, user, data, clear_state),
}


@bot.message_handler(func=lambda message: get_state(message.from_user.id) is not None, content_types=["text"])
def on_stateful_text(message):
    state_info = get_state(message.from_user.id)
    handler = TEXT_STATE_HANDLERS.get(state_info["state"])
    if not handler:
        return
    from bot.handlers.dashboard import get_or_create_user
    user = get_or_create_user(message.from_user)
    try:
        handler(message, user, state_info["data"])
    except Exception as e:  # noqa: BLE001
        log_error(message.from_user.id, e, context=state_info["state"])
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi, qayta urinib ko'ring.")


# ---------------------------------------------------------------------------
# Fayl/rasm/video/audio yuklash — faqat GroupTask topshirish kutilayotganda ishlaydi
# ---------------------------------------------------------------------------

@bot.message_handler(func=lambda message: (
    get_state(message.from_user.id) is not None
    and get_state(message.from_user.id)["state"] == GroupTaskStates.WAITING_SUBMISSION_FILE
), content_types=["document", "photo", "video", "audio", "voice"])
def on_submission_file(message):
    state_info = get_state(message.from_user.id)
    from bot.handlers.dashboard import get_or_create_user
    user = get_or_create_user(message.from_user)
    try:
        group_tasks.handle_gtask_submission_file(bot, message, user, state_info["data"], clear_state)
    except Exception as e:  # noqa: BLE001
        log_error(message.from_user.id, e, context="gtask_submission_file")
        bot.send_message(message.chat.id, "❌ Faylni qabul qilishda xatolik yuz berdi, qayta urinib ko'ring.")


# ---------------------------------------------------------------------------
# Ishga tushirish
# ---------------------------------------------------------------------------

def run():
    if settings.BOT_USE_WEBHOOK:
        logger.info("Webhook rejimida ishga tushirilmoqda: %s", settings.WEBHOOK_URL)
        bot.remove_webhook()
        bot.set_webhook(url=settings.WEBHOOK_URL)
        # Webhook rejimida bot alohida WSGI/ASGI view orqali update qabul qiladi
        # (config/urls.py ichiga tegishli endpoint qo'shiladi — production bosqichida).
    else:
        logger.info("Polling rejimida ishga tushirilmoqda...")
        bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    run()
