from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class GenderChoices(TextChoices):
    MALE = "male", _("male")
    FEMALE = "female", _("female")
    RATHER_NOT_SAY = "rather_not_say", _("rather not say")


class ServiceGenderChoices(TextChoices):
    MALE = "male", _("male")
    FEMALE = "female", _("female")
    OTHER = "other", _("other")


class ApplicationStatusChoices(TextChoices):
    PENDING = "pending", _("Pending")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")
    CANCELED = "canceled", _("Canceled")