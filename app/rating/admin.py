from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from rating import models as rating_models


@admin.register(rating_models.Rating)
class RatingAdmin(UnfoldModelAdmin):
    """
    Admin interface for the Rating model.
    """
    list_display = (
        "uid",
        "user",
        "business",
        "employee",
        "reply_to",
        "rating",
        "created_at",
    )
    search_fields = [
        "uid",
        "user__email",
        "business__name",
        "employee__name",
    ]
    readonly_fields = [
        "uid",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = [
        "user",
        "business",
        "employee",
        "reply_to",
    ]


@admin.register(rating_models.UserBusinessFavorite)
class UserBusinessFavoriteAdmin(UnfoldModelAdmin):
    """
    Admin interface for the UserBusinessFavorite model.
    """
    list_display = (
        "user",
        "business",
        "created_at",
    )
    search_fields = [
        "user__email",
        "business__name",
    ]
    readonly_fields = [
        "created_at",
    ]
    autocomplete_fields = [
        "user",
        "business",
    ]

@admin.register(rating_models.UserBusinessSave)
class UserBusinessSaveAdmin(UnfoldModelAdmin):
    """
    Admin interface for the UserBusinessSave model.
    """
    list_display = (
        "user",
        "business",
        "created_at",
    )
    search_fields = [
        "user__email",
        "business__name",
    ]
    readonly_fields = [
        "created_at",
    ]
    autocomplete_fields = [
        "user",
        "business",
    ]
    

@admin.register(rating_models.UserEmployeeFavorite)
class UserEmployeeFavoriteAdmin(UnfoldModelAdmin):
    """
    Admin interface for the UserEmployeeFavorite model.
    """
    list_display = (
        "user",
        "employee",
        "created_at",
    )
    search_fields = [
        "user__email",
        "employee__name",
    ]
    readonly_fields = [
        "created_at",
    ]
    autocomplete_fields = [
        "user",
        "employee",
    ]

