from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import StackedInline as UnfoldModelAdminInline
from leaflet.admin import LeafletGeoAdmin


from onboarding import models as onboarding_models


@admin.register(onboarding_models.Costumer)
class CostumerAdmin(UnfoldModelAdmin):
    """
    Admin interface for the Costumer model.
    """

    list_display = [
        "uid",
        "user",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "user__name",
        "user__surname",
        "user__email",
    ]
    filter_horizontal = [
        "services_interested",
    ]


@admin.register(onboarding_models.FreeLancer)
class FreeLancerAdmin(UnfoldModelAdmin, LeafletGeoAdmin):
    """
    Admin interface for the FreeLancer model.
    """

    list_display = [
        "uid",
        "user",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "user__name",
        "user__surname",
        "user__email",
    ]
    filter_horizontal = [
        "services_offered",
    ]
    list_filter = [
        "services_offered",
    ]
    list_select_related = [
        "user",
    ]


@admin.register(onboarding_models.FreelancerBusinessApply)
class FreelancerBusinessApplyAdmin(UnfoldModelAdmin):
    """
    Admin interface for the FreelancerBusinessApply model.
    """

    list_display = [
        "uid",
        "freelancer",
        "business",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "freelancer__user__email",
        "business__name",
    ]
    list_filter = [
        "status",
    ]