"""Achievements/Gamification bo'limi — to'liq."""
from django.utils import timezone

from apps.gamification.models import UserLevel, UserBadge, Streak, Badge
from services.xp_service import level_from_xp
from bot.keyboards.achievements_kb import achievements_menu_kb, leaderboard_period_kb
from bot.utils.formatters import format_xp_level
from bot.utils.callback_parser import ParsedCallback


def handle_achievements_menu(bot, call, user):
    level_info, _ = UserLevel.objects.get_or_create(user=user)
    streak, _ = Streak.objects.get_or_create(user=user)
    text = f"{format_xp_level(level_info)}\n🔥 Streak: {streak.current_daily} kun (eng uzuni: {streak.longest_daily})"
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=achievements_menu_kb(),
    )


def handle_level_info(bot, call, user):
    level_info, _ = UserLevel.objects.get_or_create(user=user)
    next_level_xp = (level_info.level ** 2) * 100  # level_from_xp formulasining teskarisi (taxminiy)
    remaining = max(0, next_level_xp - level_info.total_xp)
    text = (
        f"{format_xp_level(level_info)}\n\n"
        f"Keyingi levelgacha: ~{remaining} XP qoldi."
    )
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=achievements_menu_kb(),
    )


def handle_my_badges(bot, call, user):
    badges = UserBadge.objects.filter(user=user).select_related("badge")
    if not badges:
        text = "Hali badge yo'q. Faol bo'ling va birinchisini qo'lga kiriting! 🏅"
    else:
        text = "🏅 Sizning badgelaringiz:\n\n" + "\n".join(f"{b.badge.icon_emoji} {b.badge.title}" for b in badges)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=achievements_menu_kb(),
    )


def handle_next_goal(bot, call, user):
    earned_codes = set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))
    all_badges = Badge.objects.exclude(code__in=earned_codes)[:1]
    if all_badges:
        b = all_badges[0]
        text = f"🎯 Keyingi maqsad: {b.icon_emoji} {b.title}\n{b.description}"
    else:
        text = "🎉 Siz mavjud barcha badgelarni qo'lga kiritgansiz!"
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=achievements_menu_kb(),
    )


def handle_leaderboard(bot, call, user, cb: ParsedCallback):
    period = cb.param(0, str, "all_time")

    qs = UserLevel.objects.select_related("user")
    if period == "daily":
        from apps.gamification.models import XPTransaction
        from django.db.models import Sum
        today = timezone.localdate()
        top = (
            XPTransaction.objects.filter(created_at__date=today)
            .values("user__username", "user__full_name")
            .annotate(total=Sum("amount")).order_by("-total")[:10]
        )
        lines = [f"{i+1}. {t['user__username'] or t['user__full_name']} — {t['total']} XP" for i, t in enumerate(top)]
    else:
        top_users = qs.order_by("-total_xp")[:10]
        lines = [f"{i+1}. {u.user.display_name} — {u.total_xp} XP" for i, u in enumerate(top_users)]

    label = {"daily": "Kunlik", "weekly": "Haftalik", "monthly": "Oylik", "all_time": "Umumiy"}.get(period, period)
    text = f"🏆 Reyting ({label}):\n\n" + ("\n".join(lines) if lines else "Hali reyting bo'sh.")
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=leaderboard_period_kb(),
    )
