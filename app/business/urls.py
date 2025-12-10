from django.urls import path
from business import views as business_views
import settings


app_name = "business"

urlpatterns = [

    path("search/", business_views.SearchView.as_view(), name="business_search"),
    path("services/search/", business_views.ServiceSearchView.as_view(), name="service_search"),
    path("services/search/v2/", business_views.ServiceSearchV2View.as_view(), name="service_search_v2"),

    path("service-categories/", business_views.ServiceCategoryListView.as_view(), name="service_categories"),

    path("list/", business_views.BusinessListView.as_view(), name="business_list"),
    path("detail/<uuid:uid>/", business_views.BusinessDetailView.as_view(), name="business_detail"),

    path("services/<uuid:business_uid>/", business_views.BusinessServicesView.as_view(), name="business_services"),
    path("service/detail/<uuid:uid>/", business_views.ServiceDetailView.as_view(), name="service_detail"),
    path("employees/<uuid:business_uid>/", business_views.BusinessEmployeesView.as_view(), name="business_employees"),
    path("employee/detail/<uuid:uid>/", business_views.EmployeeDetailView.as_view(), name="employee_detail"),
    
    path("clients/<uuid:business_uid>/", business_views.BusinessClientsView.as_view(), name="business_clients"),
    path("clients/<uuid:business_uid>/v2", business_views.BusinessClientsV2View.as_view(), name="business_clients"),
    path("clients/create/", business_views.BusinessClientsCreateView.as_view(), name="business_clients_create"),
    path("client/detail/<uuid:business_uid>/<uuid:client_uid>/", business_views.BusinessClientDetailView.as_view(), name="business_client_detail"),
    path("client/edit/<uuid:uid>/", business_views.BusinessClienteditView.as_view(), name="business_client_edit"),
    path("client/delete/<uuid:uid>/", business_views.BusinessClientDeleteView.as_view(), name="business_client_delete"),

    path("client/invite/accept/<uuid:uid>/", business_views.BusinessClientInviteAcceptView.as_view(), name="business_client_invite_accept"),
    path("client/invite/ignore/<uuid:uid>/", business_views.BusinessClientInviteIgnoreView.as_view(), name="business_client_invite_ignore"),
    path("client/invite/resend/<uuid:uid>/", business_views.BusinessClientInviteResendView.as_view(), name="business_client_invite_resend"),


    path("book/", business_views.BookingView.as_view(), name="business_book"),
    path("book/add/", business_views.BookingAddView.as_view(), name="business_book_add"),
    path("book/<uuid:uid>/edit/", business_views.BookingEditView.as_view(), name="business_book_edit"),
    path("book/<uuid:uid>/delete/", business_views.BookingDeleteView.as_view(), name="business_book_delete"),
    path("book/<uuid:uid>/detail/", business_views.BookingDetailView.as_view(), name="business_book_detail"),
    path("my-bookings/", business_views.MyBookingView.as_view(), name="my_bookings"),
    path("bookings/<uuid:business_uid>/", business_views.BusinessBookingsView.as_view(), name="business_bookings"),

    path("booking-hours/me/", business_views.BookingHoursMeView.as_view(), name="booking_hours_me"),
    path("booking-hours/<uuid:business_uid>/", business_views.BookingHoursView.as_view(), name="booking_hours"),


    path("notification-settings/<uuid:business_uid>/edit/", business_views.BusinessNotificationSettingsView.as_view(), name="business_notification_settings"),


    path("working-hours/batch-update/", business_views.WorkingHoursBatchUpdateView.as_view(), name="working_hours_batch_update"),
]

test_url_patterns = [
    path("test/test-notification/trigger-book-reminder/", business_views.TestNotificationView.as_view(), name="test_notification"),
    path("test/test-notification/trigger-book-reminder/daily/", business_views.TestNotificationDailyView.as_view(), name="test_notification_daily"),
]

if settings.DEBUG:
    urlpatterns += test_url_patterns
