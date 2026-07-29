"""Groups bo'limi — to'liq: yaratish, qo'shilish, a'zolar, reyting, sozlamalar, e'lonlar."""
from django.core.paginator import Paginator
from django.db.models import Sum

from apps.groups.models import Group, GroupMembership, Announcement
from apps.gamification.models import XPTransaction
from bot.keyboards.groups_kb import (
    groups_menu_kb, my_groups_list_kb, group_detail_kb, group_tasks_kb,
    group_members_kb, member_actions_kb, group_settings_kb, announcements_kb,
)
from bot.middlewares.role_check import user_has_group_role
from bot.utils.callback_parser import ParsedCallback
from bot.states.user_states import GroupStates

PAGE_SIZE = 8


def _is_owner_or_mentor(user, group) -> bool:
    return group.owner_id == user.id or user_has_group_role(user, group, "mentor")


def handle_groups_menu(bot, call, user):
    bot.edit_message_text(
        "👥 Groups bo'limi.",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=groups_menu_kb(can_create=user.can_create_group),
    )


def handle_my_groups_list(bot, call, user):
    memberships = list(GroupMembership.objects.filter(user=user, is_active=True).select_related("group"))
    owned = Group.objects.filter(owner=user).exclude(id__in=[m.group_id for m in memberships])
    for g in owned:
        memberships.append(GroupMembership(user=user, group=g, role_in_group="mentor"))

    text = "📚 Mening guruhlarim:" if memberships else "Siz hali hech qanday guruhga a'zo emassiz."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=my_groups_list_kb(memberships),
    )


def handle_group_detail(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi.", show_alert=True)
        return
    text = (
        f"📚 {group.name}\n{group.description or '—'}\n\n"
        f"👥 A'zolar: {group.active_members_count}\n"
        f"🔑 Kod: <code>{group.invite_code}</code>\n"
        f"Holat: {'🟢 Faol' if group.is_active else '🔴 Faol emas'}"
    )
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_detail_kb(group, _is_owner_or_mentor(user, group)),
    )


# --- Yaratish (FSM) ---

def handle_group_create_start(bot, call, user, set_state):
    if not user.can_create_group:
        bot.answer_callback_query(call.id, "Guruh yaratish uchun admin ruxsati kerak.", show_alert=True)
        return
    set_state(user.telegram_id, GroupStates.WAITING_NAME, data={})
    bot.edit_message_text(
        "Guruh nomini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
    )


def handle_group_name_input(bot, message, user, state_data, set_state):
    name = message.text.strip()[:128]
    if not name:
        bot.send_message(message.chat.id, "Nom bo'sh bo'lishi mumkin emas, qayta kiriting:")
        return
    set_state(user.telegram_id, GroupStates.WAITING_DESCRIPTION, data={"name": name})
    bot.send_message(message.chat.id, "Endi guruh tavsifini kiriting (yoki '-' deb yozing, agar bo'lmasa):")


def handle_group_description_input(bot, message, user, state_data, clear_state):
    description = "" if message.text.strip() == "-" else message.text.strip()[:1000]
    name = state_data.get("name", "Nomsiz guruh")
    clear_state(user.telegram_id)

    group = Group.objects.create(name=name, description=description, owner=user)
    from apps.users.models import Role, UserRole
    owner_role, _ = Role.objects.get_or_create(name=Role.GROUP_OWNER)
    UserRole.objects.get_or_create(user=user, role=owner_role, group=group)

    bot.send_message(
        message.chat.id,
        f"✅ '{group.name}' guruhi yaratildi!\n🔑 Taklif kodi: <code>{group.invite_code}</code>\n\n"
        "Shu kodni a'zolaringizga yuboring — ular 'Kodga qo'shilish' orqali kirishadi.",
        parse_mode="HTML",
    )


def handle_join_by_code_start(bot, call, user, set_state):
    set_state(user.telegram_id, GroupStates.WAITING_INVITE_CODE, data={})
    bot.edit_message_text(
        "Guruh kodini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
    )


def handle_invite_code_input(bot, message, user, state_data, clear_state):
    code = message.text.strip().upper()
    group = Group.objects.filter(invite_code=code, is_active=True).first()
    clear_state(user.telegram_id)
    if not group:
        bot.send_message(message.chat.id, "❌ Bunday kodli guruh topilmadi.")
        return
    _, created = GroupMembership.objects.get_or_create(
        user=user, group=group, defaults={"role_in_group": GroupMembership.STUDENT}
    )
    if created:
        bot.send_message(message.chat.id, f"✅ '{group.name}' guruhiga muvaffaqiyatli qo'shildingiz!")
    else:
        bot.send_message(message.chat.id, "Siz allaqachon shu guruh a'zosisiz.")


# --- Vazifalar (guruh vazifalari ro'yxati -> gtask handlerlariga o'tadi) ---

def handle_group_tasks_list(bot, call, user, cb: ParsedCallback):
    from apps.tasks.models import GroupTask

    group_id = cb.param(0, int)
    page = cb.param(1, int, 0)
    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi.", show_alert=True)
        return
    qs = GroupTask.objects.filter(group=group).order_by("-deadline")
    page_obj = Paginator(qs, PAGE_SIZE).get_page(page + 1)
    text = "📝 Guruh vazifalari:" if page_obj.object_list else "Hozircha vazifa yo'q."
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_tasks_kb(group.id, page_obj.object_list, page, page_obj.has_next(), _is_owner_or_mentor(user, group)),
    )


# --- A'zolar ---

def handle_group_members_list(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    page = cb.param(1, int, 0)
    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi.", show_alert=True)
        return
    qs = GroupMembership.objects.filter(group=group, is_active=True).select_related("user")
    page_obj = Paginator(qs, PAGE_SIZE).get_page(page + 1)
    text = f"👥 A'zolar ({group.active_members_count}):"
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_members_kb(group.id, page_obj.object_list, page, page_obj.has_next(), group.owner_id == user.id),
    )


def handle_member_actions(bot, call, user, cb: ParsedCallback):
    membership_id = cb.param(0, int)
    membership = GroupMembership.objects.filter(id=membership_id).select_related("group", "user").first()
    if not membership or membership.group.owner_id != user.id:
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    bot.edit_message_text(
        f"👤 {membership.user.display_name} — amalni tanlang:",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=member_actions_kb(membership.id, membership.group_id),
    )


def handle_make_mentor(bot, call, user, cb: ParsedCallback):
    membership_id = cb.param(0, int)
    membership = GroupMembership.objects.filter(id=membership_id).select_related("group").first()
    if not membership or membership.group.owner_id != user.id:
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    membership.role_in_group = GroupMembership.MENTOR
    membership.save(update_fields=["role_in_group"])

    from apps.users.models import Role, UserRole
    role, _ = Role.objects.get_or_create(name=Role.MENTOR)
    UserRole.objects.get_or_create(user=membership.user, role=role, group=membership.group)

    bot.answer_callback_query(call.id, "🧑‍🏫 Mentor qilib tayinlandi.")
    handle_member_actions(bot, call, user, cb)


def handle_make_student(bot, call, user, cb: ParsedCallback):
    membership_id = cb.param(0, int)
    membership = GroupMembership.objects.filter(id=membership_id).select_related("group").first()
    if not membership or membership.group.owner_id != user.id:
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    membership.role_in_group = GroupMembership.STUDENT
    membership.save(update_fields=["role_in_group"])

    from apps.users.models import Role, UserRole
    UserRole.objects.filter(user=membership.user, role__name=Role.MENTOR, group=membership.group).delete()

    bot.answer_callback_query(call.id, "🎓 Studentga qaytarildi.")
    handle_member_actions(bot, call, user, cb)


def handle_remove_member(bot, call, user, cb: ParsedCallback):
    membership_id = cb.param(0, int)
    membership = GroupMembership.objects.filter(id=membership_id).select_related("group").first()
    if not membership or membership.group.owner_id != user.id:
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    group_id = membership.group_id
    membership.is_active = False
    membership.save(update_fields=["is_active"])
    bot.answer_callback_query(call.id, "🚪 Guruhdan chiqarildi.")
    handle_group_members_list(bot, call, user, ParsedCallback("group", "members", [group_id, 0]))


# --- Reyting ---

def handle_group_leaderboard(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi.", show_alert=True)
        return
    member_ids = GroupMembership.objects.filter(group=group, is_active=True).values_list("user_id", flat=True)
    totals = (
        XPTransaction.objects.filter(group=group, user_id__in=member_ids)
        .values("user__full_name", "user__username")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:10]
    )
    if not totals:
        text = "Bu guruhda hali reyting yo'q."
    else:
        lines = [f"{i+1}. @{t['user__username'] or t['user__full_name']} — {t['total']} XP" for i, t in enumerate(totals)]
        text = "📊 Guruh reytingi:\n\n" + "\n".join(lines)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_detail_kb(group, _is_owner_or_mentor(user, group)),
    )


# --- Sozlamalar ---

def handle_group_settings(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group or not _is_owner_or_mentor(user, group):
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    bot.edit_message_text(
        f"⚙️ '{group.name}' sozlamalari",
        chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_settings_kb(group),
    )


def handle_group_rename_start(bot, call, user, cb: ParsedCallback, set_state):
    group_id = cb.param(0, int)
    set_state(user.telegram_id, GroupStates.WAITING_NAME, data={"rename_group_id": group_id})
    bot.edit_message_text(
        "Yangi guruh nomini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
    )


def handle_group_rename_input(bot, message, user, state_data, clear_state):
    group_id = state_data.get("rename_group_id")
    group = Group.objects.filter(id=group_id).first()
    clear_state(user.telegram_id)
    if not group or not _is_owner_or_mentor(user, group):
        bot.send_message(message.chat.id, "Ruxsat yo'q.")
        return
    group.name = message.text.strip()[:128]
    group.save(update_fields=["name"])
    bot.send_message(message.chat.id, f"✅ Guruh nomi yangilandi: {group.name}")


def handle_group_toggle_active(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group or not _is_owner_or_mentor(user, group):
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    group.is_active = not group.is_active
    group.save(update_fields=["is_active"])
    bot.answer_callback_query(call.id, "🟢 Faollashtirildi." if group.is_active else "🔴 Faolsizlantirildi.")
    handle_group_settings(bot, call, user, cb)


# --- E'lonlar ---

def handle_announcements_list(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    page = cb.param(1, int, 0)
    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi.", show_alert=True)
        return
    qs = Announcement.objects.filter(group=group)
    page_obj = Paginator(qs, 5).get_page(page + 1)
    if not page_obj.object_list:
        text = "Hozircha e'lon yo'q."
    else:
        text = "\n\n".join(f"📢 {a.created_at:%d.%m.%Y}: {a.text}" for a in page_obj.object_list)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=announcements_kb(group.id, page_obj.object_list, page, page_obj.has_next()),
    )


def handle_post_announcement_start(bot, call, user, cb: ParsedCallback, set_state):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group or not _is_owner_or_mentor(user, group):
        bot.answer_callback_query(call.id, "Ruxsat yo'q.", show_alert=True)
        return
    set_state(user.telegram_id, GroupStates.WAITING_ANNOUNCEMENT_TEXT, data={"group_id": group_id})
    bot.edit_message_text(
        "E'lon matnini kiriting:", chat_id=call.message.chat.id, message_id=call.message.message_id,
    )


def handle_announcement_text_input(bot, message, user, state_data, clear_state):
    group_id = state_data.get("group_id")
    group = Group.objects.filter(id=group_id).first()
    clear_state(user.telegram_id)
    if not group:
        bot.send_message(message.chat.id, "Guruh topilmadi.")
        return
    text = message.text.strip()[:2000]
    announcement = Announcement.objects.create(group=group, author=user, text=text)

    # MUHIM: e'lon DARHOL, Celery'siz yuboriladi (send_now_bulk) — avvalgi versiyada
    # bu faqat Celery navbatiga yozilardi va Celery worker ishlamasa hech kimga
    # yetib bormasdi ("guruhga e'lon yuborish ishlamayapti" bugi shu edi).
    from apps.notifications.models import Notification
    from services.notification_service import send_now_bulk

    member_users = [
        m.user for m in GroupMembership.objects.filter(group=group, is_active=True).exclude(user=user).select_related("user")
    ]
    result = send_now_bulk(bot, member_users, Notification.ANNOUNCEMENT, f"📢 {group.name}: {text}")

    announcement.is_sent = True
    announcement.save(update_fields=["is_sent"])
    bot.send_message(
        message.chat.id,
        f"✅ E'lon yuborildi: {result['sent']} ta a'zoga yetdi"
        + (f", {result['failed']} tasiga yetmadi (botni bloklagan bo'lishi mumkin)" if result['failed'] else "")
        + (f", {result['skipped']} tasi bildirishnomani o'chirib qo'ygan" if result['skipped'] else "") + ".",
    )
