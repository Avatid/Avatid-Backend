
from rest_framework import serializers
from django_filters import rest_framework as filters
from django.db.models import Q

from business import models as business_models
from business import enums as business_enums
from user import models as user_models
from core.distance.views import Query


class BaseDistanceSortMixin:
    @staticmethod
    def resolve_distance_sort(
        queryset,
        value,
        longitude=None,
        latitude=None,
        model_field="location"):
        """
        Sorts the queryset based on distance from a given longitude and latitude.
        :param queryset: The queryset to sort.
        :param value: The sort order, either 'distance_asc' or 'distance_desc'.
        :param model_field: The field in the model that contains the location.
        :return: The sorted queryset.
        """
        if longitude is None or latitude is None:
            return queryset
        return Query.order_by_distance(
            queryset=queryset,
            longitude=longitude,
            latitude=latitude,
            model_field=model_field,
        ).order_by(value)


class ClientFilter(filters.FilterSet):

    sort_by = filters.CharFilter(
        method="resolve_sort_by",
        label="sort_by",
        required=False,
    )
    status = filters.CharFilter(
        lookup_expr="exact",
        label="Status",
        required=False,
    )

    class Meta:
        model = business_models.BusinessClient
        fields = (
            "sort_by",
            "status",
        )

    def resolve_sort_by(self, queryset, name, value):
        if value not in business_enums.ClientSortByChoices.values:
            return queryset
        return queryset.order_by(value)
    
    def filter_status(self, queryset, name, value):
        if value in business_enums.ClientStatusChoices.values:
            return queryset.filter(status=value)
        return queryset


class ServiceCategoryFilter(filters.FilterSet):
    parent_uid = filters.CharFilter(
        method="filter_parent_uid",
        label="Parent UID",
        required=False,
    )
    is_parent = filters.BooleanFilter(
        method="filter_is_parent",
        label="Is Parent",
        required=False,
    )
    name = filters.CharFilter(
        lookup_expr="icontains",
        label="Name",
        required=False,
    )
    name_en = filters.CharFilter(
        lookup_expr="icontains",
        label="Name (English)",
        required=False,
    )
    name_sq = filters.CharFilter(
        lookup_expr="icontains",
        label="Name (Albanian)",
        required=False,
    )
    uid = filters.CharFilter(
        lookup_expr="exact",
        label="UID",
        required=False,
    )

    class Meta:
        model = business_models.ServiceCategory
        fields = (
            "name",
            "uid",
            "parent_uid",
            "is_parent",
            "name_en",
            "name_sq",
        )

    def filter_parent_uid(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(parent__uid=value)
            )
        return queryset

    def filter_is_parent(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(parent__isnull=True)
            )
        return queryset


class ServiceFilter(filters.FilterSet):
    search = filters.CharFilter(
        method="filter_search",
        label="Search",
        required=False,
    )
    name = filters.CharFilter(
        lookup_expr="icontains",
        label="Name",
        required=False,
    )
    sort_by = filters.CharFilter(
        method="resolve_sort_by",
        label="sort_by",
        required=False,
    )
    categories_uids = filters.CharFilter(
        method="filter_categories_uids",
        label="Categories UIDs",
        required=False,
    )
    visit_type = filters.CharFilter(
        method="filter_visit_type",
        label="Visit Type",
        required=False,
    )
    business_type = filters.CharFilter(
        method="filter_business_type",
        label="Is Freelancer",
        required=False,
    )

    class Meta:
        model = business_models.Service
        fields = (
            "name",
            "search",
            "categories_uids",
            "visit_type",
        )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) 
        )

    def resolve_sort_by(self, queryset, name, value):
        if not value in business_enums.ServiceSortByChoices.values:
            return queryset
        if value in [
            business_enums.ServiceSortByChoices.DISTANCE_ASC.value,
            business_enums.ServiceSortByChoices.DISTANCE_DESC.value,
        ]:
            return BaseDistanceSortMixin.resolve_distance_sort(
                queryset,
                value,
                longitude=self.data.get("longitude", None),
                latitude=self.data.get("latitude", None),
                model_field="business__location"
            )
        return queryset.order_by(value)
    

    def filter_categories_uids(self, queryset, name, value):
        if value:
            categories = value.split(",")
            return queryset.filter(
                Q(category__uid__in=categories) |
                Q(category__parent__uid__in=categories)
            )
        return queryset
    
    def filter_business_type(self, queryset, name, value):
        if value in business_enums.BusinessTypeChoices.values:
            return queryset.filter(
                Q(business__business_type=value)
            )
        return queryset
    
    def filter_visit_type(self, queryset, name, value):
        if value in business_enums.VisitTypeChoices.values:
            return queryset.filter(
                Q(business__business_type=value)
            )
        return 


class EmployeeFilter(filters.FilterSet):
    search = filters.CharFilter(
        method="filter_search",
        label="Search",
        required=False,
    )
    sort_by = filters.CharFilter(
        method="resolve_sort_by",
        label="sort_by",
        required=False,
    )
    name = filters.CharFilter(
        lookup_expr="icontains",
        label="Name",
        required=False,
    )
    order_by = filters.CharFilter(
        method="resolve_order_by",
        label="order_by",
        required=False,
    )
    is_favorite = filters.BooleanFilter(
        method="filter_is_favorite",
        label="is_favorite",
        required=False,
    )

    class Meta:
        model = business_models.Employee
        fields = (
            "search",
            "name",
            "sort_by",
            "order_by",
            "is_favorite",
        )

    def resolve_order_by(self, queryset, name, value):
        if value == business_enums.OrderByChoices.NON_RATED.value:
            return queryset.filter(rating_count=0)
        if value == business_enums.OrderByChoices.RATED.value:
            return queryset.filter(rating_count__gt=0)
        if value in [
            business_enums.OrderByChoices.CANCELLED.value,
        ]:
            return queryset
        return queryset.order_by(value)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
        )

    def resolve_sort_by(self, queryset, name, value):
        if not value in business_enums.EmployeeSortByChoices.values:
            return queryset
        return queryset.order_by(value)
    
    def filter_is_favorite(self, queryset, name, value):
        return queryset.filter(is_favorite=value)


class BusinessFilter(filters.FilterSet):

    class Meta:
        model = business_models.Business
        fields = (
            "uids",
            "search",
            "name",
            "categories_uids",
            "sort_by",
            "is_favorite",
            "is_saved",
            "business_type",
        )

    uids = filters.CharFilter(
        method="filter_uids",
        label="UIDs",
        required=False,
    )
    business_type = filters.CharFilter(
        method="filter_business_type",
        label="Business Type",
        required=False,
    )
    search = filters.CharFilter(
        method="filter_search",
        label="Search",
        required=False,
    )
    categories_uids = filters.CharFilter(
        method="filter_categories_uids",
        label="Categories UIDs",
        required=False,
    )
    sort_by = filters.CharFilter(
        method="resolve_sort_by",
        label="sort_by",
        required=False,
    )
    is_favorite = filters.BooleanFilter(
        method="filter_is_favorite",
        label="is_favorite",
        required=False,
    )
    is_saved = filters.BooleanFilter(
        method="filter_is_saved",
        label="is_saved",
        required=False,
    )

    def filter_uids(self, queryset, name, value):
        if value:
            uids = value.split(",")
            return queryset.filter(
                Q(uid__in=uids)
            )
        return queryset

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(store_name__icontains=value) |
            Q(surname__icontains=value)
        )

    def filter_is_favorite(self, queryset, name, value):
        return queryset.filter(is_favorite=value)
    
    def filter_is_saved(self, queryset, name, value):
        return queryset.filter(is_saved=value)

    def filter_categories_uids(self, queryset, name, value):
        if value:
            categories = value.split(",")
            return queryset.filter(
                Q(category__uid__in=categories) |
                Q(category__parent__uid__in=categories) | 
                Q(categories__uid__in=categories)
            )
        return queryset
    
    def resolve_sort_by(self, queryset, name, value):
        if not value in business_enums.BusinessSortByChoices.values:
            return queryset
        if value in [
            business_enums.BusinessSortByChoices.DISTANCE_ASC.value,
            business_enums.BusinessSortByChoices.DISTANCE_DESC.value,
        ]:
            return BaseDistanceSortMixin.resolve_distance_sort(
                queryset,
                value,
                longitude=self.data.get("longitude", None),
                latitude=self.data.get("latitude", None),
                model_field="location"
            )
        return queryset.order_by(value)
    
    def filter_business_type(self, queryset, name, value):
        if value in business_enums.BusinessTypeChoices.values:
            return queryset.filter(
                Q(business_type=value)
            )
        return queryset
   

class UserFilter(filters.FilterSet):
    search = filters.CharFilter(
        method="filter_search",
        label="Search",
        required=False,
    )
    order_by = filters.CharFilter(
        method="resolve_order_by",
        label="order_by",
        required=False,
    )
    class Meta:
        model = user_models.User
        fields = (
            "search",
            "order_by",
        )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value)
        )
    
    def resolve_order_by(self, queryset, name, value):
        if value in [
            business_enums.OrderByChoices.RATING_ASC.value,
            business_enums.OrderByChoices.RATING_DESC.value,
            business_enums.OrderByChoices.NON_RATED.value,
            business_enums.OrderByChoices.RATED.value,
            business_enums.OrderByChoices.CANCELLED.value,
        ]:
            return queryset
        return queryset.order_by(value)


class BookingFilter(filters.FilterSet):

    bookings_uids = filters.CharFilter(
        method="filter_bookings_uids",
        label="Bookings UIDs",
        required=False,
    )
    search = filters.CharFilter(
        method="filter_search",
        label="Search",
        required=False,
    )
    order_by = filters.CharFilter(
        method="resolve_order_by",
        label="order_by",
        required=False,
    )
    client_uid = filters.CharFilter(
        method="filter_client_uid",
        label="Client UID",
        required=False,
    )
    service_uid = filters.CharFilter(
        method="filter_service_uid",
        label="Service UID",
        required=False,
    )
    start_date = filters.DateFilter(
        method="filter_start_date",
        label="Start Date",
        required=False,
    )
    end_date = filters.DateFilter(
        method="filter_end_date",
        label="End Date",
        required=False,
    )
    status = filters.CharFilter(
        lookup_expr="exact",
        label="Status",
        required=False,
    )
    class Meta:
        model = business_models.UserBusinesBooking
        fields = (
            "search",
            "order_by",
            "service_uid",
            "start_date",
            "end_date",
            "status",
        )

    def filter_bookings_uids(self, queryset, name, value):
        if value:
            bookings_uids = value.split(",")
            return queryset.filter(
                Q(uid__in=bookings_uids)
            )
        return queryset

    def filter_client_uid(self, queryset, name, value):
        return queryset.filter(
            Q(user__uid=value)
        )

    def resolve_order_by(self, queryset, name, value):
        if value in [
            business_enums.OrderByChoices.RATING_ASC.value,
            business_enums.OrderByChoices.RATING_DESC.value,
            business_enums.OrderByChoices.NAME_ASC.value,
            business_enums.OrderByChoices.NAME_DESC.value,
        ]:
            return queryset
        if value == business_enums.OrderByChoices.NON_RATED.value:
            return queryset.filter(business_rating_count=0)
        if value == business_enums.OrderByChoices.RATED.value:
            return queryset.filter(business_rating_count__gt=0)
        if value == business_enums.OrderByChoices.CANCELLED.value:
            return queryset.filter(status=business_enums.BookingStatusChoices.CANCELLED)
        return queryset.order_by(value)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(user__name__icontains=value) |
            Q(user__email__icontains=value) |
            Q(business__name__icontains=value) |
            Q(employee__name__icontains=value)
        )

    def filter_service_uid(self, queryset, name, value):
        return queryset.filter(
            Q(services__uid=value)
        )
    
    def filter_start_date(self, queryset, name, value):
        return queryset.filter(
            Q(date__gte=value)
        )
    
    def filter_end_date(self, queryset, name, value):
        return queryset.filter(
            Q(date__lte=value)
        )
    
