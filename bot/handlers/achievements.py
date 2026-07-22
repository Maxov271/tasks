"""Achievements/Gamification bo'limi."""
from apps.gamification.models import UserLevel, UserBadge
from bot.keyboards.achievements_kb import achievements_menu_kb, leaderboard_period_kb
from bot.utils.formatters import format_xp_level


def handle_achievements_menu(bot, call, user):
    level_info, _ = UserLevel.objects.get_or_create(user=user)
    bot.edit_message_text(
        format_xp_level(level_info),
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=achievements_menu_kb(),
    )


def handle_my_badges(bot, call, user):
    badges = UserBadge.objects.filter(user=user).select_related("badge")
    if not badges:
        text = "Hali badge yo'q. Faol bo'ling va birinchisini qo'lga kiriting! 🏅"
    else:
        text = "\n".join(f"{b.badge.icon_emoji} {b.badge.title}" for b in badges)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=achievements_menu_kb(),
    )


def handle_leaderboard(bot, call, user, cb):
    period = cb.param(0, str, "all_time")
    top_users = UserLevel.objects.select_related("user").order_by("-total_xp")[:10]
    lines = [f"{i+1}. {u.user.display_name} — {u.total_xp} XP" for i, u in enumerate(top_users)]
    text = f"🏆 Reyting ({period}):\n\n" + "\n".join(lines) if lines else "Hali reyting bo'sh."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=leaderboard_period_kb(),
    )
