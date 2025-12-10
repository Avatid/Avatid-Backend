from dataclasses import dataclass
from typing import Optional
from django.db.models import TextChoices


@dataclass()
class FirePush:
    push_id: str
    title: str
    body: str
    data: Optional[dict] = dict


class NotificationType(TextChoices):
    default = 'default', 'default'

