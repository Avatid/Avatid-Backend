from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import StackedInline as UnfoldModelAdminInline
from leaflet.admin import LeafletGeoAdmin

from business import models as business_models 
from business.utils.translator import TextTranslator


# ServiceCategory inline
class ServiceCategoryInline(UnfoldModelAdminInline):
    """
    Inline admin view for ServiceCategory model.
    """
    model = business_models.ServiceCategory
    extra = 0
    

@admin.register(business_models.ServiceCategory)
class ServiceCategoryAdmin(UnfoldModelAdmin):
    """
    Admin view for ServiceCategory model.
    """
    list_display = [
        "uid",
        "name",
        "name_en",
        "name_sq",
        "service_type",
        "parent",
        "description",
        "description_en",
        "description_sq",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "name",
        "name_en",
        "name_sq",
        "description",
        "description_en",
        "description_sq",
        "service_type",
    ]
    list_filter = [
        "service_type",
        "created_at",
        "updated_at",
    ]
    inlines = [ServiceCategoryInline]
    actions = ["translate_fields_action"]

    def translate_fields_action(self, request, queryset):
        fields_to_translate = ["name", "description"]
        source_lang = "en"
        target_lang = "sq"
        translator = TextTranslator(source_lang=source_lang, target_lang=target_lang)
        for obj in queryset:
            for field in fields_to_translate:
                original_text = getattr(obj, field)
                translated_text = translator.translate(original_text)
                setattr(obj, f"{field}_sq", translated_text)
            obj.save(update_fields=[f"{field}_sq" for field in fields_to_translate])
    translate_fields_action.short_description = "Translate selected fields to Albanian (sq)"


@admin.register(business_models.WorkingHours)
class WorkingHoursAdmin(UnfoldModelAdmin):
    """
    Admin view for WorkingHours model.
    """
    list_display = [
        "uid",
        "start_time",
        "end_time",
        "day_of_week",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "start_time",
        "end_time",
        "day_of_week",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]


@admin.register(business_models.SocialMedia)
class SocialMediaAdmin(UnfoldModelAdmin):
    """
    Admin view for SocialMedia model.
    """
    list_display = [
        "uid",
        "platform",
        "url",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "platform",
        "url",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]


@admin.register(business_models.Gallery)
class GalleryAdmin(UnfoldModelAdmin):
    """
    Admin view for Gallery model.
    """
    list_display = [
        "uid",
        "image",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "image",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]


@admin.register(business_models.VideoGallery)
class VideoGalleryAdmin(UnfoldModelAdmin):
    """
    Admin view for VideoGallery model.
    """
    list_display = [
        "uid",
        "video",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "video",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]


# Service inline 
class ServiceInline(UnfoldModelAdminInline):
    """
    Inline admin view for Service model.
    """
    model = business_models.Service
    extra = 0
    filter_horizontal = [
        "images",
        "working_hours",
    ]


# Employee inline
class EmployeeInline(UnfoldModelAdminInline):
    """
    Inline admin view for Employee model.
    """
    model = business_models.Employee
    extra = 0
    filter_horizontal = [
        "working_hours",
    ]


@admin.register(business_models.Service)
class ServiceAdmin(UnfoldModelAdmin):
    """
    Admin view for Service model.
    """
    list_display = [
        "uid",
        "name",
        "business",
        "price",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "name",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    filter_horizontal = [
        "images",
        "working_hours",
    ]
    autocomplete_fields = ["business"]


@admin.register(business_models.Employee)
class EmployeeAdmin(UnfoldModelAdmin):
    """
    Admin view for Employee model.
    """
    list_display = [
        "uid",
        "name",
        "business",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "name",
        "business__store_name",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = ["business", "user"]
    filter_horizontal = [
        "working_hours",
        "services",
    ]


@admin.register(business_models.Business)
class BusinessAdmin(UnfoldModelAdmin, LeafletGeoAdmin):
    """
    Admin view for Business model.
    """
    list_display = [
        "uid",
        "name",
        "store_name",
        "business_type",
        "address",
    ]
    search_fields = [
        "uid",
        "name",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    filter_horizontal = [
        "working_hours",
        "categories",
        "images",
        "socials",
        "videos",
    ]
    readonly_fields = ["metadata"]
    inlines = [ServiceInline, EmployeeInline]


@admin.register(business_models.UserBusinesBooking)
class UserBusinessBookingAdmin(UnfoldModelAdmin):
    """
    Admin view for UserBusinessBooking model.
    """
    list_display = [
        "uid",
        "user",
        "business",
        "employee",
        "date",
        "start_time",
        "end_time",
        "status",
    ]
    search_fields = [
        "uid",
        "user__email",
        "business__store_name",
        "business__uid",
        "employee__name",
        "employee__uid",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = ["user", "business", "employee"]
    filter_horizontal = [
        "services",
    ]

@admin.register(business_models.BusinessNotificationSenderSettings)
class BusinessNotificationSenderSettingsAdmin(UnfoldModelAdmin):
    """
    Admin view for BusinessNotificationSenderSettings model.
    """
    list_display = ["uid", "business", "email_notifications", "push_notifications"]
    search_fields = ["uid", "business__store_name"]
    list_filter = ["created_at", "updated_at"]
    autocomplete_fields = ["business"]


@admin.register(business_models.BusinessClient)
class BusinessClientAdmin(UnfoldModelAdmin):
    """
    Admin view for BusinessClient model.
    """
    list_display = [
        "uid",
        "user",
        "business",
        "status",
        "bio",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "uid",
        "user__email",
        "business__store_name",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = ["user", "business"]

