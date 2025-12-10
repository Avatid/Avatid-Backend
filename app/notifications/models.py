
from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

from django.contrib.auth import get_user_model

from notifications.enums import NotificationType, CostumNotificationTypeChoices, CostumNotificationObjectTypeChoices
from django.utils import timezone

from celery import current_app as celery_app


User = get_user_model()


class NotificationObject(models.Model):
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        indexes = [
            models.Index(fields=['user', 'normalized_id']),
        ]

    uid = models.UUIDField(
        verbose_name=_('uid'),
        default=uuid4,
        editable=False,
        unique=True,
    )
    normalized_id = models.TextField(
        verbose_name=_('normalized_id'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('A unique identifier for this notification to prevent duplicates.'),
    )
    push_id = models.CharField(
        verbose_name=_('push_id'),
        max_length=255,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        "user.User",
        verbose_name=_('user'),
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
    )
    body = models.TextField(
        verbose_name=_('body'),
        null=True,
        blank=True,
    )
    data = models.JSONField(
        verbose_name=_('data'),
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        verbose_name=_('notification_type'),
        choices=NotificationType.choices,
        max_length=255,
        null=True,
        blank=True,
    )
    is_sent = models.BooleanField(
        verbose_name=_('is_sent'),
        default=False,
    )
    sent_at = models.DateTimeField(
        verbose_name=_('sent_at'),
        null=True,
        blank=True,
    )
    error = models.TextField(
        verbose_name=_('error'),
        null=True,
        blank=True,
    )
    read_at = models.DateTimeField(
        verbose_name=_('read_at'),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        verbose_name=_('created_at'),
        auto_now_add=True,
        null=True,
        blank=True,
    )

    @classmethod
    def get_annotated_objects(cls):
        """
            - is_read: True if read_at is not null
        """
        return cls.objects.annotate(
            is_read=models.Case(
                models.When(read_at__isnull=False, then=True),
                default=False,
                output_field=models.BooleanField(),
            )
        )
    
    def __str__(self):
        return f'{self.title}'
    
    def mark_as_read(self):
        self.read_at = timezone.now()
        self.save()
    
    def save(self, *args, **kwargs):
        if self.is_sent and not self.sent_at:
            self.sent_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def sent_at_att(self):
        if not self.sent_at:
            return self.created_at
        return self.sent_at

    

class CostumNotification(models.Model):

    uid = models.UUIDField(
        verbose_name=_('uid'),
        default=uuid4,
        editable=False,
        unique=True,
    )
    send_to = models.ManyToManyField(
        'user.User',
        verbose_name=_('users'),
        related_name='costum_notifications',
        blank=True,
    )
    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
    )
    body = models.TextField(
        verbose_name=_('body'),
        null=True,
        blank=True,
    )
    notification_type = models.CharField(
        verbose_name=_('notification_type'),
        choices=CostumNotificationTypeChoices.choices,
        max_length=255,
        null=True,
        blank=True,
    )
    external_link = models.URLField(
        verbose_name=_('external_link'),
        null=True,
        blank=True,
        help_text=_('The link that this notification should take the user to.'),
    )
    object_type = models.CharField(
        verbose_name=_('related_object_type'),
        max_length=255,
        choices=CostumNotificationObjectTypeChoices.choices,
        null=True,
        blank=True,
        help_text=_('The type of the object that this notification is related to. eg:'),
    )
    object_uid = models.CharField(
        verbose_name=_('related_object_uid'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('The uid of the object that this notification is related to. eg: '),
    )
    object_name = models.CharField(
        verbose_name=_('related_object_name'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('The name of the object that this notification is related to.'),
    )
    genre = models.CharField(
        verbose_name=_('genre'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('The genre that this notification is related to.'),
    )
    rich_text = models.TextField(
        verbose_name=_('rich_text'),
        null=True,
        blank=True,
        help_text=_('The rich text that this notification should display.'),
    )
    preview_image = models.ImageField(
        verbose_name=_('preview_image'),
        null=True,
        blank=True,
        help_text=_('The image that this notification should display.'),
    )
    sent_at = models.DateTimeField(
        verbose_name=_('sent_at'),
        null=True,
        blank=True,
    )
    is_sent = models.BooleanField(
        verbose_name=_('is_sent'),
        default=False,
    )
    take_to_questionnaire = models.BooleanField(
        verbose_name=_('take to questionnaire'),
        default=False,
        help_text=_('If true, the notification will take the user to the questionnaire screen.'),
    )
    is_app_update = models.BooleanField(
        verbose_name=_('is_app_update'),
        default=False,
        help_text=_('If true, the notification will be considered as an app update notification.'),
    )

    @property
    def initial_data(self):
        return {
            'type': self.notification_type,
            'external_link': self.external_link if self.external_link else '',
            'object_name': self.object_name if self.object_name else '',
            'object_type': self.object_type if self.object_type else '',
            'object_uid': str(self.object_uid) if self.object_uid else '',
            'genre': self.genre if self.genre else '',
            'rich_text': self.rich_text if self.rich_text else '',
            'preview_image': self.preview_image.url if self.preview_image else '',
            'take_to_questionnaire': str(self.take_to_questionnaire),
            'is_app_update': str(self.is_app_update),
        }
    
    @property
    def users_ids(self):
        return list(self.users.values_list('id', flat=True))
    
    def mark_as_sent(self):
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()

    def __str__(self):
        return f'{self.title}'
    
    
