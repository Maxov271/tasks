from telebot import types
from bot.utils.callback_parser import build
from bot.keyboards.dashboard_kb import back_button


def calendar_month_kb(year: int, month: int, days_with_events: dict) -> types.InlineKeyboardMarkup:
    """days_with_events: {day_number: event_count}"""
    import calendar as pycalendar

    kb = types.InlineKeyboardMarkup(row_width=7)
    month_name = pycalendar.month_name[month]
    kb.row(
        types.InlineKeyboardButton("<", callback_data=build("calendar", "month", year, month - 1)),
        types.InlineKeyboardButton(f"{month_name} {year}", callback_data="noop"),
        types.InlineKeyboardButton(">", callback_data=build("calendar", "month", year, month + 1)),
    )

    week_days = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
    kb.row(*[types.InlineKeyboardButton(d, callback_data="noop") for d in week_days])

    for week in pycalendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="noop"))
            else:
                count = days_with_events.get(day, 0)
                label = f"{day} ({count})" if count else str(day)
                row.append(types.InlineKeyboardButton(label, callback_data=build("calendar", "day", year, month, day)))
        kb.row(*row)

    kb.row(back_button("dashboard"))
    return kb
