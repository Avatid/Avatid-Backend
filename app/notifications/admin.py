from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import StackedInline, TabularInline
from notifications import models as notifications_models


@admin.register(notifications_models.NotificationObject)
class NotificationObjectAdmin(UnfoldModelAdmin):
    list_display = [
        'uid',
        'normalized_id',
        'push_id',
        'user',
        'title',
        'notification_type',
        'body',
        'is_sent',
        'error',
        'sent_at',
        'read_at',
        'created_at',
    ]
    list_filter = [
        'sent_at',
        'read_at',
        'notification_type'
    ]
    search_fields = [
        'uid',
        'push_id',
        'user__email',
        'title',
        'body',
    ]
    
    readonly_fields = [
        'uid',
        'push_id',
        'user',
        'title',
        'body',
        'data',
        'notification_type',
        'is_sent',
        'sent_at',
        'error',
        'read_at',
        'created_at',
    ]


# @admin.register(notifications_models.CostumNotification)
class CostumNotificationAdmin(UnfoldModelAdmin):
    list_display = [
        'uid',
        'title',
        'notification_type',
        'body',
        'sent_at',
    ]
    list_filter = [
        'sent_at',
        'notification_type'
    ]
    search_fields = [
        'uid',
        'title',
        'body',
    ]
    readonly_fields = [
        'uid',
        'initial_data',
        'sent_at',
    ]

    filter_horizontal = [
        'send_to',
    ]

    def initial_data(self, obj):
        return obj.initial_data
