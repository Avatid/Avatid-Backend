from django.db import models
from uuid import uuid4

import settings as dj_settings
from core.models import safe_file_path



class PolicyLinks(models.Model):
    class Meta:
        verbose_name = "Policy Link"
        verbose_name_plural = "Policy Links"

    uid = models.UUIDField(unique=True, default=uuid4, editable=False)
    
    terms_and_conditions = models.URLField(
        verbose_name="Terms and Conditions",
        blank=True,
        null=True,
    )
    privacy_policy = models.URLField(
        verbose_name="Privacy Policy",
        blank=True,
        null=True,
    )
    cookie_policy = models.URLField(
        verbose_name="Cookie Policy",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.terms_and_conditions} - {self.privacy_policy} - {self.cookie_policy}"
    

    
