from django.db.models import TextChoices


class NotificationType(TextChoices):
    COSTUM = 'COSTUM', 'COSTUM'
    NEW_MESSAGE = 'NEW_MESSAGE', 'New message'
    BOOKING_CREATED = 'BOOKING_CREATED', 'BOOKING_CREATED'
    BOOKING_REMINDER = 'BOOKING_REMINDER', 'BOOKING_REMINDER'
    BOOKING_UPDATED = 'BOOKING_UPDATED', 'BOOKING_UPDATED'
    BOOKING_CANCELLED = 'BOOKING_CANCELLED', 'BOOKING_CANCELLED'
    APPLY = 'APPLY', 'APPLY'
    APPLY_RESPONSE = 'APPLY_RESPONSE', 'APPLY_RESPONSE'
    CLIENT_INVITATION = 'CLIENT_INVITATION', 'CLIENT_INVITATION'


class CostumNotificationTypeChoices(TextChoices):
    COSTUM = 'COSTUM', 'COSTUM'
    NEW_MESSAGE = 'NEW_MESSAGE', 'New message'


class CostumNotificationObjectTypeChoices(TextChoices):
    COSTUM = 'COSTUM', 'COSTUM'
    NEW_MESSAGE = 'NEW_MESSAGE', 'New message'



class OrderByChoices(TextChoices):
    NEWEST = 'newest', 'Newest'
    OLDEST = 'oldest', 'Oldest'

