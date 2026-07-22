# Telegram Productivity Workspace

Mini LMS + CRM + Task Manager + Group Management — Telegram bot (pyTelegramBotAPI) + Django + Django Admin + SQLite3 (PostgreSQL'ga tayyor).

To'liq arxitektura tavsifi uchun oldingi xabardagi hujjatga qarang. Bu — o'sha arxitekturaning ishlaydigan boshlang'ich kod skeleti.

## Loyiha holati

Bu **ishga tushirishga tayyor skelet** — barcha model, admin, servis va bot handler fayllari yozilgan, Python sintaksisi tekshirilgan. Lekin:

- Bu muhitda internet yo'qligi sababli `pip install` va `manage.py migrate` ishga tushirilmadi — buni o'zingizning kompyuteringizda bajarishingiz kerak (quyida ko'rsatilgan).
- `Focus`/Pomodoro uchun `PomodoroSession` modeli hali qo'shilmagan (arxitektura hujjatida qayd etilgan, `bot/handlers/focus.py` ichida TODO bilan belgilangan).
- Ba'zi bo'limlar (Group Task yaratish/baholash FSM oqimi, Export/Backup uchun bot handlerlari, Excel import) — servis qatlamida tayyor, lekin bot handler darajasida hali ulanmagan.

## O'rnatish

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. .env faylini sozlash
cp .env.example .env
# .env faylini oching va BOT_TOKEN'ni @BotFather'dan olingan tokenga almashtiring

# 4. Migratsiyalar
python manage.py makemigrations
python manage.py migrate

# 5. Superuser (Django Admin uchun)
python manage.py createsuperuser

# 6. Boshlang'ich ma'lumotlar (rollar)
python manage.py shell -c "
from apps.users.models import Role
for name, _ in Role.CHOICES:
    Role.objects.get_or_create(name=name)
"
```

## Ishga tushirish

```bash
# Django Admin (http://127.0.0.1:8000/admin/)
python manage.py runserver

# Telegram bot (alohida terminalda)
python bot/main.py

# Celery worker + beat (alohida terminalda, Redis ishga tushirilgan bo'lishi kerak)
celery -A tasks_celery.celery_app worker -B -l info
```

## O'zingizni birinchi Super Admin qilib belgilash

```bash
python manage.py shell -c "
from apps.users.models import User, Role, UserRole
u = User.objects.get(telegram_id=YOUR_TELEGRAM_ID)  # botga /start yozgandan keyin paydo bo'ladi
role = Role.objects.get(name=Role.SUPER_ADMIN)
UserRole.objects.get_or_create(user=u, role=role, group=None)
"
```

## Keyingi qadamlar (tavsiya etilgan tartib)

1. `python manage.py runserver` va `python bot/main.py`'ni ishga tushirib, Dashboard va Tasks bo'limini sinab ko'ring (bular to'liq ishlaydigan holatda).
2. `apps/tasks/models.py`'ga `PomodoroSession` modelini qo'shing va `bot/handlers/focus.py`'dagi TODO'larni to'ldiring.
3. `bot/handlers/groups.py`'ga guruh yaratish FSM oqimini (nom → tavsif → yaratish) qo'shing.
4. Group Task yaratish/baholash uchun mentor oqimini `bot/handlers/` ichiga alohida fayl sifatida qo'shing (`services/task_service.py`'dagi `submit_group_task`/`grade_submission` allaqachon tayyor).
5. `services/export_service.py` funksiyalarini admin panel yoki `/export` buyrug'iga ulang.
6. Production'ga chiqishdan oldin: `config/settings/prod.py`'ni sozlang, `DATABASE_URL`'ni PostgreSQL'ga yo'naltiring, `BOT_USE_WEBHOOK=True` qiling.
