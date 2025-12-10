from uuid import uuid4

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from user.geo_utils.main import GeoUtils
from onboarding import enums as onboarding_enums

from onboarding import utils as onboarding_utils


class Costumer(models.Model):
    """
    Model representing a costumer.
    """
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.OneToOneField(
        "user.User",
        on_delete=models.CASCADE,
        related_name="costumer",
    )
    services_interested = models.ManyToManyField(
        "business.ServiceCategory",
        related_name="costumers_interested",
        blank=True,
    )
    routine_data = models.JSONField(null=True, blank=True)
    gender = models.CharField(
        max_length=15,
        choices=onboarding_enums.GenderChoices.choices,
        default=onboarding_enums.GenderChoices.RATHER_NOT_SAY,
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    surname = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Costumer: {self.user}"


class FreeLancer(models.Model):
    class Meta:
        verbose_name = _("Freelancer")
        verbose_name_plural = _("Freelancers")
        ordering = ["user__name"]
        
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.OneToOneField(
        "user.User",
        on_delete=models.CASCADE,
        related_name="freelancer",
    )
    employee = models.OneToOneField(
        "business.Employee",
        on_delete=models.SET_NULL,
        related_name="freelancer",
        null=True,
        blank=True,
    )
    services_offered = models.ManyToManyField(
        "business.ServiceCategory",
        related_name="freelancers_offered",
        blank=True,
    )

    address = models.CharField(max_length=255, null=True, blank=True)
    location = models.PointField(
        verbose_name=_("Location"),
        blank=True,
        null=True,
    )
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Freelancer: {self.user}"

    def save(self, *args, **kwargs):
        if self.location and not self.longitude and not self.latitude:
            self.longitude, self.latitude = GeoUtils.point_to_coordinates(self.location)
        elif self.longitude and self.latitude and not self.location:
            self.location = GeoUtils.coordinates_to_point(self.longitude, self.latitude)
        super().save(*args, **kwargs)
    

class FreelancerBusinessApply(models.Model):
    """
    Model representing a freelancer's application to a business.
    """
    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    freelancer = models.ForeignKey(
        FreeLancer,
        on_delete=models.CASCADE,
        related_name="business_applications",
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="freelancer_applications",
    )
    status = models.CharField(
        max_length=15,
        choices=onboarding_enums.ApplicationStatusChoices.choices,
        default=onboarding_enums.ApplicationStatusChoices.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Application: {self.freelancer} to {self.business}"
    
    # on save if status is accepted, add freelancer to employee
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == onboarding_enums.ApplicationStatusChoices.APPROVED:
            onboarding_utils.add_freelancer_to_employee(
                freelancer=self.freelancer,
                business=self.business,
            )