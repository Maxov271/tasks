# Telegram Productivity Workspace

Mini LMS + CRM + Task Manager + Group Management — Telegram bot (pyTelegramBotAPI) + Django + Django Admin + SQLite3 (PostgreSQL'ga tayyor).

## Loyiha holati (yangilangan)

Barcha 12 ta bot bo'limi endi to'liq ishlaydi: Dashboard, Tasks (yaratish/tahrirlash/o'chirish/subtask/kategoriya/qidiruv), Groups (yaratish/qo'shilish/a'zolar/reyting/sozlamalar/e'lonlar), Group Tasks (uyga vazifa yaratish/topshirish/fayl yuklash/baholash), Habits, Focus/Pomodoro, Achievements, Calendar (kunni bosib o'sha kundagi vazifalarni ko'rish), Notifications, Settings, Statistics, va Admin Panel. "Bu bo'lim hali ishlab chiqilmoqda" degan xabar endi hech qaysi tugmada chiqmasligi kerak — agar chiqsa, bu bug, iltimos xabar bering.

### Nima tuzatildi

- **`task:edit` xatoligi** — dispatcher'da bu callback umuman ro'yxatdan o'tmagan edi, shuning uchun tugma bossangiz xatolik/"ishlab chiqilmoqda" chiqardi. Endi to'liq tahrirlash menyusi (nom/tavsif/prioritet/deadline) ishlaydi.
- **`require_role` decoratori** — bot handlerlariga noto'g'ri parametr tartibida yozilgan edi, shu sabab Admin Panel ba'zan ishlamasligi mumkin edi. Tuzatildi.
- **Mentor/Group Owner uchun noto'g'ri "🛠 Admin Panel" tugmasi** — bu tugma faqat global Admin/Super Admin uchun ko'rsatiladi endi (mentor/owner o'z guruhini "Groups → guruh → ⚙️ Sozlamalar" orqali boshqaradi).
- **`📈 Statistics` tugmasi** — hech qanday handler'ga ulanmagan edi, endi shaxsiy statistika (bajarilgan vazifalar, streak, XP, fokus vaqti) to'liq ishlaydi.
- **Custom deadline kiritish** — "✍️ Sana kiritish" tugmasi bosilganda foydalanuvchiga matn kiritish so'ralar edi, lekin bot buni kutmas edi (FSM holati o'rnatilmagan edi). Tuzatildi.
- **Guruh yaratuvchisi noto'g'ri rol olardi** (Mentor o'rniga Group Owner bo'lishi kerak edi).
- **Kalendar** — endi kunni bosganda o'sha kundagi barcha vazifalar/hodisalar ro'yxati ochiladi, va kunlar holatga qarab ranglanadi (pastga qarang).

### Telegram tugma ranglari haqida muhim eslatma

Telegram Bot API **inline tugmalarning fon rangini o'zgartirish imkonini bermaydi** — bu Telegram platformasining o'zining texnik cheklovi, kutubxona yoki bizning kod bilan bog'liq emas. Shuning uchun "rang berish" so'rovingizni ijodiy tarzda **rangli doira emojilar** orqali amalga oshirdim:

- Vazifalar ro'yxatida: ✅ bajarilgan, 🔴 muddati o'tgan, 🟢/🟡/🟠/🔴 — prioritetga qarab
- Kalendarda kunlar: 🔴 muddati o'tgan vazifasi bor kun, 🟠 bugun, 🟡 kelgusidagi reja bor kun, 🟢 hammasi bajarilgan kun
- Admin panelda: 🚫 ban qilingan, ⭐ premium, 🟢/🔴 — guruh faol/faol emas
- Guruh a'zolari: 👑 owner, 🧑‍🏫 mentor, 🎓 student
- Guruh vazifalari: 🟡 kutilmoqda, ✅ baholangan, 🔴 kechikkan

Bu vizual jihatdan real ranglash imkonini bermasa-da, foydalanuvchiga bir qarashda holatni "ranglar" orqali yetkazadi.

## .env fayliga qanday ma'lumot kiritiladi

`.env` fayli loyiha ildizida (`manage.py` bilan bir joyda) joylashadi. Namuna uchun `.env.example`'ni nusxalang:

```bash
cp .env.example .env
```

| O'zgaruvchi | Nima uchun kerak | Qayerdan olinadi |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django'ning ichki kriptografik kaliti (session, CSRF va h.k.) | O'zingiz tasodifiy uzun matn yozing, yoki `python -c "import secrets; print(secrets.token_urlsafe(50))"` bilan generatsiya qiling |
| `ALLOWED_HOSTS` | Django'ga qaysi domenlardan so'rov qabul qilish mumkinligini aytadi | Production domeningiz, masalan `myproject.alwaysdata.net` |
| `BOT_TOKEN` | Telegram bot tokeni | Telegram'da **@BotFather**'ga `/newbot` yozib oling |
| `BOT_USE_WEBHOOK` | `False` — polling rejimi (oddiy, lokal test uchun qulay); `True` — webhook rejimi (production uchun tavsiya etiladi) | O'zingiz tanlaysiz |
| `WEBHOOK_URL` | Faqat `BOT_USE_WEBHOOK=True` bo'lsa kerak — botga so'rov keladigan HTTPS manzil | `https://sizning-domeningiz/bot-webhook/` kabi |
| `CELERY_BROKER_URL` | Celery qaysi Redis'ga ulanishi | Odatda `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery natijalarni qayerga yozishi | Odatda `redis://localhost:6379/1` |
| `DATABASE_URL` | **Faqat production** (`config/settings/prod.py`) uchun — PostgreSQL'ga ulanish satri | `postgres://user:parol@host:5432/baza_nomi` |

**Muhim:** `.env` fayli hech qachon Git'ga qo'shilmasin (`.gitignore`'da allaqachon bor). U faqat sizning serveringizda/kompyuteringizda turadi.

## O'rnatish (lokal)

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. .env
cp .env.example .env
# .env faylini oching, BOT_TOKEN va DJANGO_SECRET_KEY'ni to'ldiring

# 4. Migratsiyalar
python manage.py makemigrations
python manage.py migrate

# 5. Standart rollarni yaratish (Super Admin, Admin, Mentor, Group Owner, User)
python manage.py bootstrap_roles

# 6. Django Admin uchun superuser (bu — Django'ning o'z admin login tizimi,
#    botdagi "Super Admin" roli bilan ARALASHTIRMANG, ular alohida narsa)
python manage.py createsuperuser
```

## Ishga tushirish

```bash
# Django Admin panel (http://127.0.0.1:8000/admin/)
python manage.py runserver

# Telegram bot (alohida terminalda)
python bot/main.py

# Celery worker + beat — eslatmalar, backup, statistika uchun (alohida terminalda, Redis kerak)
celery -A tasks_celery.celery_app worker -B -l info
```

## Botga Admin foydalanuvchi tayinlash — 2 usul

### 1-usul: Django Admin panel orqali (so'ralgan, eng qulay)

1. Foydalanuvchi botga kamida bir marta `/start` yozgan bo'lishi kerak (shundagina u bazada paydo bo'ladi).
2. `http://127.0.0.1:8000/admin/` (yoki production manzilingiz) ga kiring.
3. **Users → Users** bo'limiga o'ting.
4. Kerakli foydalanuvchi(lar)ni belgilang (checkbox).
5. Pastdagi **Action** ochiladigan menyusidan **"🛠 Adminlikka tayinlash (global)"** ni tanlang va **Go** tugmasini bosing.
   - Super Admin qilish uchun **"👑 Super Adminlikka tayinlash"** ni tanlang.
   - Rolni olib tashlash uchun **"🗑 Global Admin/Super Admin rollarini olib tashlash"**.
6. Foydalanuvchi ro'yxatidagi **"Rollar"** ustunida yangi rol darhol ko'rinadi.

Shu bilan birga, har bir foydalanuvchi sahifasini alohida ochib, pastdagi **"User roles"** inline jadvali orqali ham istalgan rolni (jumladan guruhga xos Mentor/Group Owner rollarini) qo'lda qo'shishingiz mumkin.

### 2-usul: Terminal buyrug'i orqali (birinchi Super Admin uchun tezkor yo'l)

Loyihani birinchi marta sozlaganda, Django Admin'ga kirish uchun ham kimdir Super Admin bo'lishi kerak — shu holatda:

```bash
python manage.py set_super_admin <telegram_id>
```

`<telegram_id>`ni Telegram'dagi [@userinfobot](https://t.me/userinfobot) orqali bilib olishingiz mumkin.

## AlwaysData'ga yuklash — ketma-ketlik

AlwaysData Django, PostgreSQL, Celery/Redis va uzoq muddat ishlaydigan "daemon" (User program) jarayonlarini rasman qo'llab-quvvatlaydi — bot va Celery worker'ni alohida "site" sifatida ro'yxatdan o'tkazish orqali ishga tushirish mumkin.

1. **Hisob va SSH.** alwaysdata.com'da hisob oching. Administration panelidan SSH login/parolingizni oling va ulaning:
   ```bash
   ssh sizning_login@ssh-sizning_login.alwaysdata.net
   ```

2. **PostgreSQL baza yaratish.** Administration → **Databases** → **Add a database** → PostgreSQL tanlang, nom bering. Login ma'lumotlarini eslab qoling (`DATABASE_URL`ga kerak bo'ladi).

3. **Kodni yuklash.** SSH orqali yoki Git orqali (agar loyihangiz GitHub'da bo'lsa, `git clone` bilan) `www/` papkangiz ichiga joylashtiring.

4. **Virtual environment va kutubxonalar:**
   ```bash
   cd ~/www/telegram_workspace
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **`.env` faylini serverga yozing** (yuqoridagi jadvaldagi barcha qiymatlar bilan, `DATABASE_URL`ni PostgreSQL ma'lumotlaringiz bilan to'ldirib):
   ```
   DATABASE_URL=postgres://login:parol@postgresql-sizning_login.alwaysdata.net:5432/baza_nomi
   ```

6. **Migratsiya va statik fayllar:**
   ```bash
   DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py migrate
   DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py collectstatic --noinput
   DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py bootstrap_roles
   DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py createsuperuser
   ```

7. **Django Admin uchun sayt yarating** (Web → Sites → Add a site):
   - Type: **Python WSGI**
   - Application path: `config/wsgi.py` fayliga yo'l
   - Environment: `DJANGO_SETTINGS_MODULE=config.settings.prod` qo'shing
   - Addresses: sizga ajratilgan `*.alwaysdata.net` manzilini yoki custom domeningizni bog'lang

8. **Telegram bot uchun alohida sayt yarating** (bot doim ishlab turishi kerak, shuning uchun "User program" turi mos):
   - Type: **User program**
   - Command: `/home/sizning_login/www/telegram_workspace/venv/bin/python bot/main.py`
   - Working directory: `telegram_workspace/` papkangiz
   - Environment: `DJANGO_SETTINGS_MODULE=config.settings.prod`

   Muqobil variant — `BOT_USE_WEBHOOK=True` qilib, botni Django WSGI saytining o'zi ichiga webhook endpoint sifatida ulash (bu holda `config/urls.py`ga webhook view qo'shish kerak bo'ladi — polling oddiyroq va kichik/o'rta bot uchun to'liq yetarli).

9. **Celery worker uchun yana bitta "User program" sayt:**
   - Command: `/home/sizning_login/www/telegram_workspace/venv/bin/celery -A tasks_celery.celery_app worker -B -l info`
   - AlwaysData Redis'ni alohida instans sifatida taqdim etadi — Administration → Databases bo'limidan Redis yarating va manzilini `.env`dagi `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`ga yozing.

10. **Har bir kod o'zgarishidan keyin** tegishli saytni Administration panelidan **Restart** qiling (AlwaysData avtomatik qayta yuklamaydi).

**Eslatma:** agar Celery/Redis sozlash murakkab tuyulsa, AlwaysData'ning o'z **Scheduled tasks** (Timer) funksiyasidan foydalanib, `tasks_celery/reminders.py`dagi funksiyalarni chaqiradigan oddiy Django management buyruqlarini har daqiqada/soatda ishga tushirish orqali ham xuddi shu natijaga (eslatmalar, backup) erishish mumkin — bu Celery'siz, faqat cron-uslubidagi oddiyroq yechim.

## Bilinigan kamchiliklar va tavsiya etilgan keyingi qadamlar

- **Excel/PDF/CSV export** (`services/export_service.py`) tayyor, lekin hali bot tugmasiga ulanmagan — Admin Panel yoki Tasks bo'limiga "📤 Export" tugmasi qo'shish tavsiya etiladi.
- **Webhook rejimi** uchun `config/urls.py`ga real webhook endpoint hali qo'shilmagan (hozircha faqat polling to'liq ishlaydi).
- **Rate limiter** (`bot/middlewares/rate_limit.py`) hozircha bitta process xotirasida ishlaydi — agar botni bir nechta worker/process bilan ishga tushirsangiz, Redis-based versiyaga almashtirish kerak bo'ladi.
- **In-memory FSM state** (`bot/main.py`dagi `_user_states`) bot qayta ishga tushganda tozalanadi — production'da Redis-based saqlashga o'tkazish tavsiya etiladi (kod tuzilishi bunga tayyor: faqat `set_state/get_state/clear_state` funksiyalarini Redis bilan almashtirish kifoya).
- **Broadcast** katta (10 000+) foydalanuvchi bazasida `enqueue_notification`'ni bitta-bitta chaqirish o'rniga `bulk_create` bilan optimallashtirilishi mumkin.
