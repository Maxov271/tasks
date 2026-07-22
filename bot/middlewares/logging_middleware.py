"""Har bir callback/xabar uchun structured logging."""
import logging

logger = logging.getLogger("bot")


def log_update(update_type: str, telegram_id: int, payload: str):
    logger.info("update=%s user=%s payload=%s", update_type, telegram_id, payload)


def log_error(telegram_id: int, error: Exception, context: str = ""):
    logger.exception("XATO user=%s context=%s error=%s", telegram_id, context, error)
