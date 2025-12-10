from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from leaflet.admin import LeafletGeoAdmin

from user import models

# unregister unnecessary models
from django.contrib.auth.admin import GroupAdmin
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin, BlacklistedTokenAdmin
OutstandingTokenAdmin.has_module_permission = lambda self, request: False
BlacklistedTokenAdmin.has_module_permission = lambda self, request: False
GroupAdmin.has_module_permission = lambda self, request: False


@admin.register(models.User)
class UserAdmin(UnfoldModelAdmin, LeafletGeoAdmin):
    readonly_fields = [
        "uid",
        "created_at",
        "last_login",

        "longitude",
        "latitude",
        "user_role",
    ]
    search_fields = [
        "email",
        "name",
        "surname",
        "uid",
    ]
    list_display = (
        "uid",
        "name",
        "surname",
        "email",
        "phone",
        "is_email_verified",
        "is_phone_verified",
        "created_at",
    )
    fields = [
        "uid",
        "notification_settings",
        "email",
        "name",
        "phone",
        "is_staff",
        "is_email_verified",
        "is_phone_verified",
        "password",
        "is_active",
        "avatar_id",
        "current_location",
        "created_at",
        "last_login",

        "longitude",
        "latitude",

        "chosen_role",
        "user_role",
        "timezone",
        "lang_code",
    ]

    def user_role(self, obj):
        return obj.user_role

    def has_delete_permission(self, request, obj=None):
        return obj != request.user
    
    def longitude(self, obj):
        return obj.current_location.x
    
    def latitude(self, obj):
        return obj.current_location.y

    # on save if password is not encrypted encrypt it
    def save_model(self, request, obj, form, change):
        if not obj.password:
            obj.save()
        if obj.password and not obj.password.startswith("pbkdf2_sha256"):
            obj.set_password(obj.password)
        obj.save()


@admin.register(models.UserNotificationSettings)
class NotificationSettingsAdmin(UnfoldModelAdmin):
    list_display = (
        "user",
    )
    search_fields = [
        "user__email",
    ]


@admin.register(models.UserPushToken)
class UserPushTokenAdmin(UnfoldModelAdmin):
    list_display = (
        "user",
        "push_id",
    )
    search_fields = [
        "user__email",
    ]


@admin.register(models.UserDevice)
class UserDeviceAdmin(UnfoldModelAdmin):
    list_display = (
        "user",
        "device_id",
        "is_blacklisted",
    )
    search_fields = [
        "user__email",
        "device_id",
    ]
    list_filter = (
        "is_blacklisted",
    )

