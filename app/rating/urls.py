from django.urls import path
from rating import views as rating_views

app_name = "rating"

urlpatterns = [
    path("add/", rating_views.AddRatingView.as_view(), name="add_rating"),

    path("list/<uuid:business_uid>/", rating_views.RatingListView.as_view(), name="list_rating"),
    path("list/booking/<uuid:booking_uid>/", rating_views.RatingBookingListView.as_view(), name="list_booking_rating"),
    path("list/employee/<uuid:employee_uid>/", rating_views.RatingEmployeeListView.as_view(), name="list_employee_rating"),
    
    path("replies/<uuid:rating_uid>/", rating_views.RatingRepliesView.as_view(), name="list_rating_replies"),
    path("delete/<uuid:uid>/", rating_views.DeleteRatingView.as_view(), name="delete_rating"),
    path("edit/<uuid:uid>/", rating_views.EditRatingView.as_view(), name="edit_rating"),

    path("my-rating/", rating_views.MyRatingView.as_view(), name="my_rating"),

    path("save/", rating_views.SaveBusinessView.as_view(), name="save_business"),
    path("unsave/<uuid:business_uid>/", rating_views.UnsaveBusinessView.as_view(), name="unsave_business"),
    path("favorite/", rating_views.FavoriteBusinessView.as_view(), name="favorite_business"),
    path("unfavorite/<uuid:business_uid>/", rating_views.UnfavoriteBusinessView.as_view(), name="unfavorite_business"),

    path("favorite/employee/", rating_views.FavoriteEmployeeView.as_view(), name="favorite_employee"),
    path("unfavorite/employee/<uuid:employee_uid>/", rating_views.UnfavoriteEmployeeView.as_view(), name="unfavorite_employee"),
]
