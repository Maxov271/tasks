"""Foydalanuvchiga ko'rsatiladigan matnlarni formatlash uchun umumiy funksiyalar."""

PRIORITY_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"}


def format_task_line(task) -> str:
    emoji = PRIORITY_EMOJI.get(task.priority, "⚪")
    status = "✅" if task.is_done else ("⏰" if task.is_overdue else "🔹")
    deadline = task.deadline.strftime("%d.%m %H:%M") if task.deadline else "muddatsiz"
    return f"{status} {emoji} {task.title} — {deadline}"


def progress_bar(done: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "▓" * 0 + "░" * length + " 0/0"
    filled = round(length * done / total)
    bar = "▓" * filled + "░" * (length - filled)
    return f"{bar} {done}/{total}"


def format_xp_level(level_info) -> str:
    return f"🏆 Level {level_info.level} · {level_info.total_xp} XP"
