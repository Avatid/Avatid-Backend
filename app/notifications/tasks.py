from celery import shared_task
from typing import List
from notifications.schemas import FirePush
from notifications.fire_push import FirePush, PushSchema, MsgSchema
from notifications import models as notifications_models
from notifications.enums import NotificationType
from notifications.task_sender import NotificationTaskSender


@shared_task(name='send_fire_push')
def send_fire_push_task(fire_push_schema: dict):
    print('send_fire_push_task')
    fire_push_schema = PushSchema(**fire_push_schema)
    print(fire_push_schema)
    FirePush().send_multicast_message(fire_push_schema)
    print('send_fire_push_task done')

