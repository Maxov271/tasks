"""
XP, level va streak bilan bog'liq barcha biznes-logika shu yerda jamlangan —
bot handlerlari ham, Django Admin action'lari ham shu servisdan foydalanadi
(logikani ikki joyda takrorlamaslik uchun).
"""
import math

from django.db import transaction

from apps.gamification.models import XPTransaction, UserLevel, Streak, Badge, UserBadge

# XP manbalari va miqdorlari (arxitektura hujjatining 7-bo'limiga mos)
XP_RULES = {
    "task_done": 10,
    "task_done_on_time_bonus": 5,
    "homework_submitted": 20,
    "streak_daily_bonus": 2,
    "streak_weekly_bonus": 15,
    "pomodoro_session": 5,
}


def level_from_xp(total_xp: int) -> int:
    """Progressiv formula: har keyingi level oldingisidan ko'proq XP talab qiladi."""
    return max(1, int(math.isqrt(total_xp // 100)) + 1)


@transaction.atomic
def add_xp(user, amount: int, reason: str, group=None) -> UserLevel:
    """Foydalanuvchiga XP qo'shadi, UserLevel'ni yangilaydi va streak'ni faollashtiradi."""
    XPTransaction.objects.create(user=user, amount=amount, reason=reason, group=group)

    level_info, _ = UserLevel.objects.select_for_update().get_or_create(user=user)
    level_info.total_xp = max(0, level_info.total_xp + amount)
    level_info.level = level_from_xp(level_info.total_xp)
    level_info.save()

    streak, _ = Streak.objects.get_or_create(user=user)
    streak.register_activity()

    check_and_award_badges(user)
    return level_info


def check_and_award_badges(user):
    """Oddiy threshold-based badge tekshiruvi. Katta loyihada bu qoidalar
    alohida BadgeRule modeliga chiqarilishi mumkin, hozircha kod ichida."""
    level_info = getattr(user, "level_info", None)
    streak = getattr(user, "streak", None)

    candidates = []
    if level_info and level_info.total_xp >= 1000:
        candidates.append("1000_xp")
    if streak and streak.current_daily >= 30:
        candidates.append("30_day_streak")

    for code in candidates:
        badge = Badge.objects.filter(code=code).first()
        if badge:
            UserBadge.objects.get_or_create(user=user, badge=badge)
