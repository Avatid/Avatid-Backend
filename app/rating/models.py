from uuid import uuid4

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from rating import enums as rating_enums


class Rating(models.Model):

    uid = models.UUIDField(default=uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    booking = models.ForeignKey(
        "business.UserBusinesBooking",
        on_delete=models.CASCADE,
        related_name="ratings",
        null=True,
        blank=True,
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="ratings",
        null=True,
        blank=True,
    )
    employee = models.ForeignKey(
        "business.Employee",
        on_delete=models.CASCADE,
        related_name="ratings",
        null=True,
        blank=True,
    )
    rating = models.IntegerField(
        choices=rating_enums.RatingChoices.choices,
        null=True,
        blank=True,
    )
    comment = models.TextField(null=True, blank=True)
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Rating")
        verbose_name_plural = _("Ratings")

    def __str__(self):
        return f"{self.uid}"
    

class UserBusinessFavorite(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User Business Favorite")
        verbose_name_plural = _("User Business Favorites")
        unique_together = ("user", "business")

    def __str__(self):
        return f"{self.user} favorited {self.business}"


class UserBusinessSave(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="saves",
    )
    business = models.ForeignKey(
        "business.Business",
        on_delete=models.CASCADE,
        related_name="saves",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User Business Save")
        verbose_name_plural = _("User Business Saves")
        unique_together = ("user", "business")

    def __str__(self):
        return f"{self.user} saved {self.business}"
    

class UserEmployeeFavorite(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="employee_favorites",
    )
    employee = models.ForeignKey(
        "business.Employee",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("User Employee Favorite")
        verbose_name_plural = _("User Employee Favorites")
        unique_together = ("user", "employee")

    def __str__(self):
        return f"{self.user} favorited {self.employee}"
