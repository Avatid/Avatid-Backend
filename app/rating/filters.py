
from rest_framework import serializers
from django_filters import rest_framework as filters
from django.db.models import Q

from rating import models as rating_models
from rating import enums as rating_enums


class RatingFilter(filters.FilterSet):
    """
    FilterSet for filtering ratings.
    """
    booking_uid = filters.CharFilter(
        method="filter_booking_uid",
        label="Booking UID",
        required=False,
    )
    business_uid = filters.CharFilter(
        method="filter_business_uid",
        label="Business UID",
        required=False,
    )
    employee_uid = filters.CharFilter(
        method="filter_employee_uid",
        label="Employee UID",
        required=False,
    )
    reply_to_uid = filters.CharFilter(
        method="filter_reply_to_uid",
        label="Reply To UID",
        required=False,
    )
    sort_by = filters.CharFilter(
        method='filter_sort_by',
        label='Sort By',
        required=False,
    )

    class Meta:
        model = rating_models.Rating
        fields = (
            "business_uid",
            "employee_uid",
            "reply_to_uid",
        )

    def filter_sort_by(self, queryset, name, value):
        if value not in rating_enums.SortByChoices.values:
            return queryset
        return queryset.order_by(
            value
        )

    def filter_business_uid(self, queryset, name, value):
        if value:
            return queryset.filter(business__uid=value)
        return queryset

    def filter_employee_uid(self, queryset, name, value):
        if value:
            return queryset.filter(employee__uid=value)
        return queryset
    
    def filter_reply_to_uid(self, queryset, name, value):
        if value:
            return queryset.filter(reply_to__uid=value)
        return queryset
    
    def filter_booking_uid(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(booking__uid=value) | Q(reply_to__booking__uid=value)
            )
        return queryset