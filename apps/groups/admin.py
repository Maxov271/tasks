from django.contrib import admin
from .models import Group, GroupMembership, Announcement


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "invite_code", "active_members_count", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "invite_code", "owner__full_name")
    inlines = [GroupMembershipInline]
    readonly_fields = ("invite_code",)


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "group", "role_in_group", "is_active")
    list_filter = ("role_in_group", "is_active")
    search_fields = ("user__full_name", "group__name")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "author", "is_sent", "created_at")
    list_filter = ("is_sent",)
