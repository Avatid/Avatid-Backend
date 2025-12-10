from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional, List, Union

from firebase_admin.messaging import Message, Notification, send
from firebase_admin.messaging import Notification, MulticastMessage, \
    send_each_for_multicast, BatchResponse

from django.utils import timezone
from django.contrib.auth import get_user_model

from notifications import models as notifications_models
from user.models import UserPushToken

from notifications.firebase_client import FireBaseClient

User = get_user_model()

# DOCS:     https://github.com/firebase/firebase-admin-python/blob/master/snippets/messaging/cloud_messaging.py
# REQUIRED: /app/service-account-file.json
class PushType(str, Enum):
    DEFAULT = 'default'


class MsgSchema(BaseModel):
    push_id: Union[str, List[str]]
    data: Optional[dict] = Field(default_factory=dict)

    @property
    def parsed_data(self):
        """
        Convert all data values to string to avoid errors on the firebase admin side.
        """
        for key in self.data:
            if not isinstance(self.data[key], str):
                self.data[key] = str(self.data[key])
        return self.data


class PushSchema(MsgSchema):
    title: str
    body: str

push_app = FireBaseClient.CLIENT


class FirePush:

    @staticmethod
    def send_push(fire_push: PushSchema, notifications_instances=None):
        if not notifications_instances:
            notifications_instances = []
        
        o = 'send_push'
        if not fire_push.data.get('click_action'):
            fire_push.data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

        message = Message(
            notification=Notification(
                title=fire_push.title,
                body=fire_push.body,
            ),
            token=fire_push.push_id,
            data=fire_push.parsed_data
        )
        notification = FirePush.create_notification_object(fire_push)
        try:
            send(message)
            print("Sent push notification successfully")
            FirePush.mark_notification_as_sent(notification)
        except Exception as e:
            print(f"Error sending push notification: {e}")
            FirePush.mark_notification_as_fail(notification, str(e))

        notifications_instances.append(notification)
        FirePush.create_notification_objects_batch(notifications_instances)

    @staticmethod
    def send_msg(fire_msg: MsgSchema):
        o = 'send_msg'
        if not fire_msg.data.get('click_action'):
            fire_msg.data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

        message = Message(
            token=fire_msg.push_id,
            data=fire_msg.data
        )
        try:
            send(message)
            print("Sent push notification successfully")
        except Exception as e:
            print(f"Error sending push notification: {e}")
    
    @classmethod
    def send_push_batch(cls, msgs_batch : List[dict]):
        notifications_instances = []
        o = 'send_push_batch'
        for msg in msgs_batch:
            cls.send_push(msg, notifications_instances)

    @staticmethod
    def create_notification_object(notification: PushSchema, normalized_id=None) -> notifications_models.NotificationObject:
        if not normalized_id:
            normalized_id = f"{timezone.now().timestamp()}-{notification.title}-{notification.body}"
        token = UserPushToken.objects.filter(push_id=notification.push_id).first()
        if not token:
            user = None
        else:
            user = token.user
        instance = notifications_models.NotificationObject(
            push_id=notification.push_id,
            normalized_id=normalized_id,
            user=user,
            title=notification.title,
            body=notification.body,
            data=notification.data,
            notification_type=notification.data.get('type'),
        )
        return instance
    
    @staticmethod
    def mark_notification_as_sent(notification: notifications_models.NotificationObject, commit=False):
        notification.is_sent = True
        notification.sent_at = timezone.now()
        if commit:
            notification.save()

    @staticmethod
    def mark_notification_as_fail(notification: notifications_models.NotificationObject, error: str, commit=False):
        notification.is_sent = False
        notification.error = error
        if commit:
            notification.save()

    @staticmethod
    def create_notification_objects_batch(notifications: List[notifications_models.NotificationObject]):
        if not notifications or len(notifications) == 0:
            return
        notifications_models.NotificationObject.objects.bulk_create(notifications)
        print("Created notification objects successfully")

    @classmethod
    def send_multicast_message(cls, message: PushSchema):
        """
        Sending multicast message for all devices
        """
        normalized_id = f"{timezone.now().timestamp()}-{message.title}-{message.body}"
        tokens = [message.push_id] if isinstance(message.push_id, str) else message.push_id
        multicast_message = MulticastMessage(
            data=message.data,
            tokens=tokens,
            notification=Notification(
                title=message.title,
                body=message.body,
            ),
        )
        notif_logs = [
            cls.create_notification_object(
                PushSchema(push_id=token, title=message.title, body=message.body, data=message.data),
                normalized_id=normalized_id,
            ) for token in tokens
        ]
        failed_tokens = []
        error_logs = []
        result: BatchResponse = send_each_for_multicast(multicast_message)
        if result.failure_count > 0:
            responses = result.responses
            for idx, resp in enumerate(responses):
                if not resp.success:
                    print(f"Failed to send notification with: {resp.exception}")
                    failed_tokens.append(tokens[idx])
                    error_logs.append(str(resp.exception))
            UserPushToken.objects.filter(push_id__in=failed_tokens).delete()
            tokens = set(tokens) - set(failed_tokens)
        cls.log_notifications(notif_logs, failed_tokens, error_logs)
        return result
    
    @classmethod
    def log_notifications(cls, notif_logs: List[notifications_models.NotificationObject], failed_tokens=[], error_logs=[]):
        failed_notif_logs = [notif for notif in notif_logs if notif.push_id in failed_tokens]
        success_notif_logs = [notif for notif in notif_logs if notif.push_id not in failed_tokens]
        for notif in failed_notif_logs:
            cls.mark_notification_as_fail(notif, error_logs[failed_tokens.index(notif.push_id)])
        for notif in success_notif_logs:
            cls.mark_notification_as_sent(notif)
        cls.create_notification_objects_batch(notif_logs)
        print("Logged notifications successfully")