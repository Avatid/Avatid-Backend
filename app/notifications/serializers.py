from typing import List, Optional

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from notifications.task_sender import NotificationTaskSender
from notifications import models as notifications_models

from user import models as user_models


class PushTokenSerializer(serializers.ModelSerializer):
    def create(self, validated_data: dict):
        validated_data.update(
            {
                'user': self.context["request"].user
            }
        )
        return super().create(validated_data)

    class Meta:
        model = user_models.UserPushToken
        fields = ('push_id',)


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.BooleanField()

    sent_at = serializers.DateTimeField(source='sent_at_att', read_only=True)


    class Meta:
        model = notifications_models.NotificationObject
        fields = [
            'uid',
            'push_id',
            'title',
            'notification_type',
            'body',
            'data',
            'sent_at',
            'read_at',
            'is_read',
        ]


class NotificationMarkReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = notifications_models.NotificationObject
        fields = [
            'uid',
        ]
    
    def update(self, instance, validated_data):
        """
        Marks the notification as read
        """
        instance.mark_as_read()
        return instance


