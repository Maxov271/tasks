"""
FSM holatlari — matn/fayl kiritish talab qilinadigan joylarda ishlatiladi.
Saqlash uchun pyTelegramBotAPI'ning custom_state_storage (yoki Redis-based
StateMemoryStorage) ishlatiladi; bu yerda faqat holat nomlari va state uchun
vaqtinchalik ma'lumot strukturasi belgilanadi.
"""


class TaskStates:
    WAITING_TITLE = "task:waiting_title"
    WAITING_DESCRIPTION = "task:waiting_description"
    WAITING_CUSTOM_DEADLINE = "task:waiting_custom_deadline"
    WAITING_SUBTASK_TITLE = "task:waiting_subtask_title"
    WAITING_EDIT_TITLE = "task:waiting_edit_title"
    WAITING_EDIT_DESC = "task:waiting_edit_desc"
    WAITING_SEARCH_QUERY = "task:waiting_search_query"
    WAITING_CATEGORY_NAME = "task:waiting_category_name"


class GroupStates:
    WAITING_NAME = "group:waiting_name"
    WAITING_DESCRIPTION = "group:waiting_description"
    WAITING_INVITE_CODE = "group:waiting_invite_code"
    WAITING_ANNOUNCEMENT_TEXT = "group:waiting_announcement_text"


class GroupTaskStates:
    WAITING_TITLE = "gtask:waiting_title"
    WAITING_DEADLINE = "gtask:waiting_deadline"
    WAITING_SUBMISSION_FILE = "gtask:waiting_submission_file"
    WAITING_GRADE_SCORE = "gtask:waiting_grade_score"
    WAITING_GRADE_COMMENT = "gtask:waiting_grade_comment"


class HabitStates:
    WAITING_NAME = "habit:waiting_name"


class AdminStates:
    WAITING_BROADCAST_TEXT = "admin:waiting_broadcast_text"
    WAITING_BAN_REASON = "admin:waiting_ban_reason"


# Har bir holat qanday "keyingi qadam" funksiyaga bog'langanini saqlaydigan registry.
# bot/main.py ichida register_next_step_handler yoki custom middleware shu yordamida ishlaydi.
STATE_HANDLERS = {}


def register_state_handler(state: str):
    def decorator(func):
        STATE_HANDLERS[state] = func
        return func
    return decorator
