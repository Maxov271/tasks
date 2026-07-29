import os
import dj_database_url
from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# PostgreSQL'ga o'tish — faqat DATABASE_URL environment o'zgaruvchisini sozlash yetarli,
# model kodiga hech qanday tegish shart emas.
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.parse(DATABASE_URL, conn_max_age=600)

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
