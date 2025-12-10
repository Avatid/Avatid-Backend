from django.contrib import admin
import settings
from django.conf.urls.static import static
from django.urls import path, include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

admin.site.site_header = f"{settings.PROJECT_NAME} administration"
admin.site.index_title = f"{settings.PROJECT_NAME} administration"
admin.site.site_title = f"{settings.PROJECT_NAME}"
admin.site.site_url = ""

# Swagger
swagger_patterns = path(
    "api/schema/",
    include(
        [
            path("", SpectacularAPIView.as_view(), name="schema"),
            path(
                "swagger/",
                SpectacularSwaggerView.as_view(url_name="schema"),
                name="swagger",
            ),
        ]
    ),
)

# API patterns
api_patterns = path(
    "api/",
    include(
        [
            path("notifications/", include("notifications.urls")),
            path("user/", include("user.urls")),
            path("shared/", include("shared.urls")),
            path("sms/", include("sms.urls")),
            path("business/", include("business.urls")),
            path("onboarding/", include("onboarding.urls")),
            path("rating/", include("rating.urls")),
        ]
    ),
)


urlpatterns = [
    api_patterns,
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns.append(swagger_patterns)
    
