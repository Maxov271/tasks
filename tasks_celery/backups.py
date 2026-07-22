"""SQLite backup — Python sqlite3.Connection.backup() orqali, consistent va lock qilmasdan."""
import sqlite3
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone


@shared_task
def run_daily_backup(keep_last_n: int = 14):
    from apps.core.models import BotSetting  # placeholder — real BackupRecord modeli qo'shilishi mumkin

    backup_dir = Path(settings.BASE_DIR) / "backups"
    backup_dir.mkdir(exist_ok=True)

    db_path = settings.DATABASES["default"]["NAME"]
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        return  # PostgreSQL'da bu task ishlamaydi — pg_dump asosidagi alohida task kerak

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_{timestamp}.sqlite3"

    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(backup_path))
    with dst:
        src.backup(dst)
    src.close()
    dst.close()

    # Eski backup'larni rotatsiya qilish
    backups = sorted(backup_dir.glob("backup_*.sqlite3"), reverse=True)
    for old in backups[keep_last_n:]:
        old.unlink()
