
from notifications import views as notification_views
from django.urls import path
from settings import DEBUG

app_name = 'notifications'

urlpatterns = [
    path('push_token/', notification_views.PushTokenCreateView.as_view(), name='push_token_create'),
    path('my-notifications/', notification_views.MyNotificationsListView.as_view(), name='my-notifications'),
    path('clear-all-notifications/', notification_views.ClearAllNotificationsView.as_view({'delete':'delete'}), name='clear-all-notifications'),
    path('clear-notification/<str:uid>/', notification_views.ClearNotificationView.as_view(), name='clear-notification'),
    path('mark-as-read/<str:uid>/', notification_views.MarkAsReadView.as_view(), name='mark-as-read'),
]
