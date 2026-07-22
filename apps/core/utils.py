"""
apps/core ichidagi umumiy yordamchi funksiyalar (ID generatsiya, sana formatlash va h.k.).
"""
import random
import string


def generate_invite_code(length: int = 8) -> str:
    """Guruh uchun noyob (deyarli) invite kod generatsiya qiladi. Chaqiruvchi tomonda
    unique constraint tekshiruvi bilan birga qo'llanilishi kerak (collision holatida qayta chaqirish)."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def format_deadline(dt) -> str:
    """Sana/vaqtni foydalanuvchiga chiroyli ko'rsatish uchun formatlaydi."""
    if dt is None:
        return "belgilanmagan"
    return dt.strftime("%d.%m.%Y %H:%M")
