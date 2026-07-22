"""Groups bo'limi. tasks.py bilan bir xil naqsh: menu -> list -> detail -> actions."""
from apps.groups.models import Group, GroupMembership
from bot.keyboards.groups_kb import groups_menu_kb, group_detail_kb
from bot.utils.callback_parser import ParsedCallback


def handle_groups_menu(bot, call, user):
    bot.edit_message_text(
        "👥 Groups bo'limi.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=groups_menu_kb(can_create=user.can_create_group),
    )


def handle_my_groups_list(bot, call, user):
    memberships = GroupMembership.objects.filter(user=user, is_active=True).select_related("group")
    if not memberships:
        text = "Siz hali hech qanday guruhga a'zo emassiz."
    else:
        text = "\n".join(f"• {m.group.name}" for m in memberships)
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=groups_menu_kb(can_create=user.can_create_group),
    )


def handle_group_detail(bot, call, user, cb: ParsedCallback):
    group_id = cb.param(0, int)
    group = Group.objects.filter(id=group_id).first()
    if not group:
        bot.answer_callback_query(call.id, "Guruh topilmadi.", show_alert=True)
        return
    is_owner_or_mentor = group.owner_id == user.id or GroupMembership.objects.filter(
        group=group, user=user, role_in_group=GroupMembership.MENTOR
    ).exists()
    text = (
        f"📚 {group.name}\n{group.description}\n\n"
        f"👥 A'zolar: {group.active_members_count}\n"
        f"🔑 Kod: {group.invite_code}"
    )
    bot.edit_message_text(
        text, chat_id=call.message.chat.id, message_id=call.message.message_id,
        reply_markup=group_detail_kb(group, is_owner_or_mentor),
    )


def handle_join_by_code_start(bot, call, user, set_state):
    from bot.states.user_states import GroupStates
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
    GroupMembership.objects.get_or_create(user=user, group=group, defaults={"role_in_group": GroupMembership.STUDENT})
    bot.send_message(message.chat.id, f"✅ '{group.name}' guruhiga muvaffaqiyatli qo'shildingiz!")
