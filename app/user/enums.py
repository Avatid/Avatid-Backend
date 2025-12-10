from enum import Enum
from django.db.models import TextChoices


class UserSecurityCode(str, Enum):
    REFRESH_PASSWORD = "REFRESH_PASSWORD"
    VERIFY_EMAIL = "VERIFY_EMAIL"
    RESET_PASSWORD = "RESET_PASSWORD"


class UserSocialInfoChoices(str, Enum):
    GOOGLE = "GOOGLE"
    FACEBOOK = "FACEBOOK"
    APPLE = "APPLE"
    INSTAGRAM = "INSTAGRAM"


class UserRoleChoices(TextChoices):
    BUSINESS = "BUSINESS", "BUSINESS"
    COSTUMER = "CUSTOMER", "CUSTOMER"
    FREELANCER = "FREELANCER", "FREELANCER"

