from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.dev"
)