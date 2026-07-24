from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button

WEEK_DAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def _day_color(status: str) -> str:
    """
    Telegram inline tugmalar haqiqiy fon rangini qo'llab-quvvatlamaydi —
    shuning uchun holatni rangli doira emoji bilan 'ranglab' ko'rsatamiz:
    🔴 muddati o'tgan/bugungi zudlik, 🟠 bugun, 🟡 kelgusida, 🟢 hammasi bajarilgan.
    """
    return {
        "overdue": "🔴", "today": "🟠", "upcoming": "🟡", "done": "🟢", "none": "",
    }.get(status, "")


def calendar_month_kb(year: int, month: int, day_status: dict) -> types.InlineKeyboardMarkup:
    """day_status: {day_number: "overdue"|"today"|"upcoming"|"done"} — kalendar shu asosida ranglanadi."""
    import calendar as pycalendar

    kb = types.InlineKeyboardMarkup(row_width=7)
    month_name = pycalendar.month_name[month]
    kb.row(
        types.InlineKeyboardButton("◀️", callback_data=build("calendar", "month", year, month - 1)),
        types.InlineKeyboardButton(f"{month_name} {year}", callback_data="noop"),
        types.InlineKeyboardButton("▶️", callback_data=build("calendar", "month", year, month + 1)),
    )
    kb.row(*[types.InlineKeyboardButton(d, callback_data="noop") for d in WEEK_DAYS])

    for week in pycalendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="noop"))
            else:
                status = day_status.get(day)
                color = _day_color(status)
                label = f"{color}{day}" if color else str(day)
                row.append(types.InlineKeyboardButton(label, callback_data=build("calendar", "day", year, month, day)))
        kb.row(*row)

    kb.row(
        types.InlineKeyboardButton("📅 Bugun", callback_data=build("calendar", "today")),
        back_button("dashboard"),
    )
    return kb


def calendar_day_kb(year: int, month: int, day: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("➕ Shu kunga vazifa qo'shish", callback_data=build("calendar", "add_task", year, month, day)),
    )
    kb.add(back_button(f"calendar:month:{year}:{month}"))
    return kb
