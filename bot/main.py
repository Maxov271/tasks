"""
Bot ishga tushirish nuqtasi. Ishlatish:

    DJANGO_SETTINGS_MODULE=config.settings.dev python bot/main.py

Bu fayl:
1) Django'ni sozlaydi (ORM'ga kirish uchun majburiy — bot alohida process
   bo'lsa ham, xuddi shu modellardan foydalanadi),
2) telebot instance yaratadi,
3) barcha callback_data'larni domain bo'yicha tegishli handler'ga yo'naltiradi
   (markazlashgan dispatcher — har bir handler faylida o'z ichida routing yo'q).
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
    dashboard, tasks, groups, habits, focus, achievements,
    calendar as calendar_handlers, notifications, settings as settings_handlers, admin,
)
from bot.middlewares.rate_limit import is_rate_limited  # noqa: E402
from bot.middlewares.logging_middleware import log_update, log_error  # noqa: E402
from bot.utils.callback_parser import parse  # noqa: E402

logger = logging.getLogger("bot")
bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")

# In-memory FSM holat saqlash (kichik loyiha uchun yetarli; katta yuklamada
# Redis-based storage'ga almashtiriladi — interfeys shu ikki funksiya orqali izolatsiya qilingan)
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
        "back": lambda call, user, cb: dashboard.handle_dashboard_callback(bot, call, user),
        "cancel": lambda call, user, cb: (clear_state(user.telegram_id), dashboard.handle_dashboard_callback(bot, call, user)),
    },
    "task": {
        "menu": lambda call, user, cb: tasks.handle_tasks_menu(bot, call, user),
        "list": lambda call, user, cb: tasks.handle_task_list(bot, call, user, cb),
        "list_done": lambda call, user, cb: tasks.handle_task_list_done(bot, call, user, cb),
        "view": lambda call, user, cb: tasks.handle_task_view(bot, call, user, cb),
        "done": lambda call, user, cb: tasks.handle_task_done(bot, call, user, cb),
        "create": lambda call, user, cb: tasks.handle_task_create_start(bot, call, user, set_state),
        "set_priority": lambda call, user, cb: tasks.handle_set_priority(bot, call, user, cb),
        "set_deadline": lambda call, user, cb: tasks.handle_set_deadline_quick(bot, call, user, cb),
    },
    "group": {
        "menu": lambda call, user, cb: groups.handle_groups_menu(bot, call, user),
        "my_list": lambda call, user, cb: groups.handle_my_groups_list(bot, call, user),
        "view": lambda call, user, cb: groups.handle_group_detail(bot, call, user, cb),
        "join_by_code": lambda call, user, cb: groups.handle_join_by_code_start(bot, call, user, set_state),
    },
    "habit": {
        "menu": lambda call, user, cb: habits.handle_habits_menu(bot, call, user),
        "check_today": lambda call, user, cb: habits.handle_check_today(bot, call, user),
    },
    "focus": {
        "menu": lambda call, user, cb: focus.handle_focus_menu(bot, call, user),
        "start": lambda call, user, cb: focus.handle_focus_start(bot, call, user, cb),
    },
    "ach": {
        "menu": lambda call, user, cb: achievements.handle_achievements_menu(bot, call, user),
        "my_badges": lambda call, user, cb: achievements.handle_my_badges(bot, call, user),
        "leaderboard": lambda call, user, cb: achievements.handle_leaderboard(bot, call, user, cb),
    },
    "calendar": {
        "menu": lambda call, user, cb: calendar_handlers.handle_calendar_menu(bot, call, user),
        "month": lambda call, user, cb: calendar_handlers.handle_calendar_month(bot, call, user, cb),
    },
    "notif": {
        "menu": lambda call, user, cb: notifications.handle_notif_menu(bot, call, user),
        "toggle": lambda call, user, cb: notifications.handle_notif_toggle(bot, call, user, cb),
    },
    "settings": {
        "menu": lambda call, user, cb: settings_handlers.handle_settings_menu(bot, call, user),
    },
    "profile": {
        "menu": lambda call, user, cb: settings_handlers.handle_profile_menu(bot, call, user),
    },
    "admin": {
        "menu": lambda call, user, cb: admin.handle_admin_menu(bot, call, user),
        "users": lambda call, user, cb: admin.handle_admin_users_list(bot, call, user, cb),
        "ban": lambda call, user, cb: admin.handle_admin_ban(bot, call, user, cb),
    },
}


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

    domain_map = DOMAIN_HANDLERS.get(cb.domain)
    action_func = domain_map.get(cb.action) if domain_map else None
    if not action_func:
        bot.answer_callback_query(call.id, "Bu bo'lim hali ishlab chiqilmoqda 🚧")
        return

    try:
        action_func(call, user, cb)
        bot.answer_callback_query(call.id)
    except PermissionError as e:
        bot.answer_callback_query(call.id, str(e), show_alert=True)
    except Exception as e:  # noqa: BLE001
        log_error(call.from_user.id, e, context=call.data)
        bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi, qayta urinib ko'ring.")


# ---------------------------------------------------------------------------
# FSM matn kiritish handler'i (state kutilayotgan har qanday matn xabar shu yerga tushadi)
# ---------------------------------------------------------------------------

from bot.states.user_states import TaskStates, GroupStates  # noqa: E402

TEXT_STATE_HANDLERS = {
    TaskStates.WAITING_TITLE: lambda message, user, data: tasks.handle_task_title_input(
        bot, message, user, data, set_state, clear_state
    ),
    GroupStates.WAITING_INVITE_CODE: lambda message, user, data: groups.handle_invite_code_input(
        bot, message, user, data, clear_state
    ),
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
