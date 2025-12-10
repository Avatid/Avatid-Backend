from notifications import models as notifications_models
from notifications.task_sender import NotificationTaskSender

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=notifications_models.CostumNotification)
def post_save_costum_notification(sender, instance, created, **kwargs):
    print("post_save_costum_notification")
    if not instance.is_sent:
        NotificationTaskSender.send_costum_notification(instance)