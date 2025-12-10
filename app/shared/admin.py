from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin

from shared import models as shared_models


@admin.register(shared_models.PolicyLinks)
class PolicyLinksAdmin(UnfoldModelAdmin):
    list_display = ("terms_and_conditions", "privacy_policy", "cookie_policy")

    def has_add_permission(self, request):
        if shared_models.PolicyLinks.objects.count() == 0:
            return True
        return False
    
