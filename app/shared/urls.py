from django.urls import path
from shared import views as shared_views

app_name = "shared"

urlpatterns = [
   path("policy-links/", shared_views.PolicyLinksView.as_view(), name="policy-links"),
]
