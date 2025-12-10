from modeltranslation.translator import register, TranslationOptions

from business import models as business_models


@register(business_models.ServiceCategory)
class ServiceCategoryTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )
