import datetime

from django.db.models import Q
from django.utils.translation import gettext_lazy as _


from rest_framework import generics
from rest_framework.serializers import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django_filters import rest_framework as drf_filters

from celery import current_app as celery_app

from core.distance.views import DistanceView

from business import models as business_models
from business import enums as business_enums
from business import serializers as business_serializers
from business.utils import registry as business_registry
from business.utils.bookings import BookingHoursBuilder
from business import filters as business_filters
from user import models as user_models


class SearchView(generics.ListAPIView):
    """
    API view to search for businesses.
    """
    serializer_class = business_serializers.SearchListSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="data_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.SearchDataTypeChoices],
                description="Type of data to search for",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search",
                required=False,
            ),
            OpenApiParameter(
                name="order_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.OrderByChoices],
                description="Order by",
                required=False,
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start Date",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End Date",
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.BookingStatusChoices],
                description="Status of the booking",
                required=False,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        data_type = self.request.query_params.get("data_type", business_enums.SearchDataTypeChoices.ALL.value)
        
        clients = []
        employees = []
        bookings = []
        user = self.request.user
        business = business_models.Business.objects.filter(user=user).first()

        if data_type in [
            business_enums.SearchDataTypeChoices.CLIENT.value,
            business_enums.SearchDataTypeChoices.ALL.value,
        ]:
            if business:
                clients = business_registry.BusinessRegistry.get_annotated_business_clients(
                    business_uid=business.uid,
                )
        
        if data_type in [
            business_enums.SearchDataTypeChoices.EMPLOYEE.value,
            business_enums.SearchDataTypeChoices.ALL.value,
        ]:
            employees = business_registry.EmployeeRegistry.get_annotated_employees(
                user=user,
            )

        if data_type in [
            business_enums.SearchDataTypeChoices.BOOKING.value,
            business_enums.SearchDataTypeChoices.ALL.value,
        ] and business:
            bookings = business_models.UserBusinesBooking.objects.filter(
                business=business,
            )
        
        if clients:
            clients = business_filters.UserFilter(
                self.request.query_params,
                queryset=clients,
            ).qs
        
        if employees:
            employees = business_filters.EmployeeFilter(
                self.request.query_params,
                queryset=employees,
            ).qs

        if bookings:
            bookings = business_filters.BookingFilter(
                self.request.query_params,
                queryset=bookings,
            ).qs

        final_qs = list(clients) + list(employees) + list(bookings)
        return final_qs


class ServiceSearchView(generics.ListAPIView):
    """
    API view to search for services.
    """
    serializer_class = business_serializers.ServiceListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.ServiceFilter
    
    def get_queryset(self):
        return business_registry.ServiceRegistry.get_annotated_services()

    @classmethod
    def get_near_me(cls, request, queryset):
        longitude = request.query_params.get("longitude", None)
        latitude = request.query_params.get("latitude", None)
        distance = request.query_params.get("distance", None)

        if longitude is None or latitude is None or distance is None:
            return queryset
        
        return DistanceView.resolve_geolocation_filter(
            queryset,
            longitude=longitude,
            latitude=latitude,
            distance=distance,
            model_field="business__location",
        )
    
    def get_queryset(self):
        self.queryset = business_registry.ServiceRegistry.get_annotated_services(
           user=self.request.user,
        )
        return self.get_near_me(self.request, self.queryset).distinct()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="longitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Longitude of the location to search around",
                required=False,
            ),
            OpenApiParameter(
                name="latitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Latitude of the location to search around",
                required=False,
            ),
            OpenApiParameter(
                name="distance",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Distance (in km) to cover around the specified location",
                required=False,
                default=1.0,
            ),
            OpenApiParameter(
                name="sort_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort by field",
                enum=[item.value for item in business_enums.ServiceSortByChoices],
                required=False,
            ),
            OpenApiParameter(
                name="categories_uids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of category UIDs to filter by",
                required=False,
            ),
            OpenApiParameter(
                name="visit_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Visit type to filter by",
                enum=[item.value for item in business_enums.VisitTypeChoices],
                required=False,
            ),
            OpenApiParameter(
                name="business_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Business type to filter by",
                enum=[item.value for item in business_enums.BusinessTypeChoices],
                required=False,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)



class ServiceSearchV2View(generics.ListAPIView):
    """
    API view to search for services with additional filters.
    """
    serializer_class = business_serializers.ServicesSearchListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    
    def get_queryset(self):
        return business_registry.ServiceRegistry.get_annotated_services()

    @classmethod
    def get_near_me(cls, request, queryset, model_field="location"):
        longitude = request.query_params.get("longitude", None)
        latitude = request.query_params.get("latitude", None)
        distance = request.query_params.get("distance", None)

        if longitude is None or latitude is None or distance is None:
            return queryset
        
        return DistanceView.resolve_geolocation_filter(
            queryset,
            longitude=longitude,
            latitude=latitude,
            distance=distance,
            model_field=model_field,
        )
    
    def get_queryset(self):
        data_type = self.request.query_params.get(
            "data_type", business_enums.SearchDataTypeChoices.ALL.value
        )
        services = []
        business = []
        near_me_services = []
        near_me_business = []
        near_me_business_collaboration = []
        merged_business = []
        
        if data_type in [
            business_enums.SearchDataTypeChoices.SERVICE.value,
            business_enums.SearchDataTypeChoices.ALL.value,
        ]:
            services = business_registry.ServiceRegistry.get_annotated_services(
                user=self.request.user,
            )
        if data_type in [
            business_enums.SearchDataTypeChoices.BUSINESS.value,
            business_enums.SearchDataTypeChoices.ALL.value,
        ]:
            business = business_registry.BusinessRegistry.get_annotated_business(
                user=self.request.user,
            )
        if services:
            services = business_filters.ServiceFilter(
                self.request.query_params,
                queryset=services,
            ).qs
        if business:
            business = business_filters.BusinessFilter(
                self.request.query_params,
                queryset=business,
            ).qs
        
        if services:
            near_me_services = self.get_near_me(
                self.request,
                services,
                model_field="business__location",
            )
        if business:
            near_me_business = self.get_near_me(
                self.request,
                business,
                model_field="location",
            )
            near_me_business_collaboration = self.get_near_me(
                self.request,
                business,
                model_field="collaboration_location",
            )
        if near_me_business and near_me_business_collaboration:
            merged_business = near_me_business | near_me_business_collaboration
        final_qs = list(near_me_services) + list(merged_business)
        return final_qs

        
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="data_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[
                    business_enums.SearchDataTypeChoices.BUSINESS.value, 
                    business_enums.SearchDataTypeChoices.SERVICE.value, 
                    business_enums.SearchDataTypeChoices.ALL.value
                ],
                description="Type of data to search for",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search",
                required=False,
            ),
            OpenApiParameter(
                name="longitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Longitude of the location to search around",
                required=False,
            ),
            OpenApiParameter(
                name="latitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Latitude of the location to search around",
                required=False,
            ),
            OpenApiParameter(
                name="distance",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Distance (in km) to cover around the specified location",
                required=False,
                default=1.0,
            ),
            OpenApiParameter(
                name="sort_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort by field",
                enum=[item.value for item in business_enums.ServiceSortByChoices],
                required=False,
            ),
            OpenApiParameter(
                name="categories_uids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of category UIDs to filter by",
                required=False,
            ),
            OpenApiParameter(
                name="visit_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Visit type to filter by",
                enum=[item.value for item in business_enums.VisitTypeChoices],
                required=False,
            ),
            OpenApiParameter(
                name="business_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Business type to filter by",
                enum=[item.value for item in business_enums.BusinessTypeChoices],
                required=False,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ServiceCategoryListView(generics.ListAPIView):
    """
    API view to list all service categories.
    """
    serializer_class = business_serializers.ServiceCategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = business_models.ServiceCategory.objects.all()
    pagination_class = None
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.ServiceCategoryFilter


class BookingView(generics.CreateAPIView):

    """
    API view to create a new booking.
    """
    serializer_class = business_serializers.BookingCreateSerializer
    permission_classes = [IsAuthenticated]


class BookingAddView(generics.CreateAPIView):
    """
    API view to add a new booking.
    """
    serializer_class = business_serializers.BookingAddSerializer
    permission_classes = [IsAuthenticated]


class BookingEditView(generics.UpdateAPIView):
    """
    API view to edit an existing booking.
    """
    serializer_class = business_serializers.BookingEditSerializer
    queryset = business_models.UserBusinesBooking.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"
    allowed_methods = ["PATCH"]


class BookingDeleteView(generics.DestroyAPIView):
    """
    API view to delete an existing booking.
    """
    queryset = business_models.UserBusinesBooking.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"


class BookingDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a booking by its UID.
    """
    serializer_class = business_serializers.BookingListSerializer
    permission_classes = [IsAuthenticated]
    queryset = business_models.UserBusinesBooking.objects.all()
    lookup_field = "uid"


class MyBookingView(generics.ListAPIView):
    """
    API view to list all bookings for the authenticated user.
    """
    serializer_class = business_serializers.BookingListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.BookingFilter

    def get_queryset(self):
        return business_models.UserBusinesBooking.get_annotated_queryset(
            user=self.request.user,
        ).filter(
            user=self.request.user,
        ).order_by("date", "start_time")
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="bookings_uids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of booking UIDs to filter by",
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.BookingStatusChoices],
                description="Status of the booking",
                required=False,
            ),
            OpenApiParameter(
                name="service_uid",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Service UID",
                required=False,
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start Date",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End Date",
                required=False,
            ),
            OpenApiParameter(
                name="order_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.OrderByChoices],
                required=False
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class BusinessBookingsView(generics.ListAPIView):
    """
    API view to list all bookings for a specific business.
    """
    serializer_class = business_serializers.BookingListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.BookingFilter

    def get_queryset(self):
        business_uid = self.kwargs.get("business_uid")
        return business_models.UserBusinesBooking.get_annotated_queryset(
            user=self.request.user,
        ).filter(
            business__uid=business_uid,
        ).order_by("date", "start_time")

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="bookings_uids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of booking UIDs to filter by",
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.BookingStatusChoices],
                description="Status of the booking",
                required=False,
            ),
            OpenApiParameter(
                name="service_uid",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Service UID",
                required=False,
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start Date",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End Date",
                required=False,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BusinessListView(generics.ListAPIView):
    """
    API view to list all businesses.
    """
    serializer_class = business_serializers.BusinessListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.BusinessFilter


    @classmethod
    def get_near_me(cls, request, queryset):
        longitude = request.query_params.get("longitude", None)
        latitude = request.query_params.get("latitude", None)
        distance = request.query_params.get("distance", None)

        if longitude is None or latitude is None or distance is None:
            return queryset
        
        location_queryset = DistanceView.resolve_geolocation_filter(
            queryset,
            longitude=longitude,
            latitude=latitude,
            distance=distance,
            model_field="location",
        )
        collaboration_location_queryset = DistanceView.resolve_geolocation_filter(
            queryset,
            longitude=longitude,
            latitude=latitude,
            distance=distance,
            model_field="collaboration_location",
        )
        merged_queryset = location_queryset | collaboration_location_queryset
        return merged_queryset
    
    def get_queryset(self):
        self.queryset = business_registry.BusinessRegistry.get_annotated_business(
           user=self.request.user,
        )
        return self.get_near_me(self.request, self.queryset).distinct()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="longitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Longitude of the location to search around",
                required=False,
            ),
            OpenApiParameter(
                name="latitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Latitude of the location to search around",
                required=False,
            ),
            OpenApiParameter(
                name="distance",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Distance (in km) to cover around the specified location",
                required=False,
                default=1.0,
            ),
            OpenApiParameter(
                name="sort_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort by field",
                enum=[item.value for item in business_enums.BusinessSortByChoices],
                required=False,
            ),
            OpenApiParameter(
                name="categories_uids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of category UIDs to filter by",
                required=False,
            ),
            OpenApiParameter(
                name="uids",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of business UIDs to filter by",
                required=False,
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by favorite status",
                required=False,
            ),
            OpenApiParameter(
                name="is_saved",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by saved status",
                required=False,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class BusinessDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a business by its UID.
    """
    serializer_class = business_serializers.BusinessDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"

    def get_queryset(self):
        return business_registry.BusinessRegistry.get_annotated_business(
           user=self.request.user,
        )


class BusinessServicesView(generics.ListAPIView):
    """
    API view to list all services for a specific business.
    """
    serializer_class = business_serializers.ServiceListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.ServiceFilter

    def get_queryset(self):
        business_uid = self.kwargs.get("business_uid")
        return business_models.Service.objects.filter(business__uid=business_uid).prefetch_related(
            "images",
            "working_hours",
        )


class ServiceDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a service by its UID.
    """
    serializer_class = business_serializers.ServiceListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"

    def get_queryset(self):
        return business_models.Service.objects.all().prefetch_related(
            "images",
            "working_hours",
        )


class BusinessEmployeesView(generics.ListAPIView):
    """
    API view to list all employees for a specific business.
    """
    serializer_class = business_serializers.EmployeeListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.EmployeeFilter

    def get_queryset(self):
        business_uid = self.kwargs.get("business_uid")
        return business_registry.EmployeeRegistry.get_annotated_employees(
            user=self.request.user,
        ).filter(
            business__uid=business_uid
        )
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="sort_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort by field",
                enum=[item.value for item in business_enums.EmployeeSortByChoices],
                required=False,
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by favorite status",
                required=False,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class EmployeeDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve an employee by its UID.
    """
    serializer_class = business_serializers.EmployeeListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"

    def get_queryset(self):
        return business_registry.EmployeeRegistry.get_annotated_employees(
            user=self.request.user,
        )
    

class BusinessClientsView(generics.ListAPIView):
    """
    API view to list all clients for a specific business.
    """
    serializer_class = business_serializers.ClientListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"

    def get_queryset(self):
        business_uid = self.kwargs.get("business_uid")
        return business_registry.BusinessRegistry.get_annotated_business_clients(
            business_uid=business_uid,
        )
    

class BusinessClientsV2View(generics.ListAPIView):
    """
    API view to list all clients for a specific business with additional booking details.
    """
    serializer_class = business_serializers.ClientListV2Serializer
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = business_filters.ClientFilter

    def get_queryset(self):
        business_uid = self.kwargs.get("business_uid")
        return business_registry.ClientRegistry.get_annotated_clients(
            business_uid=business_uid,
        ).filter(
            business__uid=business_uid,
        )
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="sort_by",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Sort by field",
                enum=[item.value for item in business_enums.ClientSortByChoices],
                required=False,
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=[item.value for item in business_enums.ClientStatusChoices],
                description="Filter by client status",
                required=False,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BusinessClientsCreateView(generics.CreateAPIView):
    """
    API view to create a new client for a specific business.
    """
    serializer_class = business_serializers.BusinessClientCreateSerializer
    permission_classes = [IsAuthenticated]


class BusinessClientDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve a client by its UID.
    """
    serializer_class = business_serializers.ClientListV2Serializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        business_uid = self.kwargs.get("business_uid")
        return business_registry.ClientRegistry.get_annotated_clients(
            business_uid=business_uid,
        )
    
    def get_object(self):
        client_uid = self.kwargs.get("client_uid")
        queryset = self.get_queryset()
        return queryset.filter(
            Q(
                uid=client_uid,
            ) | Q(
                user__uid=client_uid,
            )
        ).first()
            


class BusinessClienteditView(generics.UpdateAPIView):
    """
    API view to edit an existing client for a specific business.
    """
    serializer_class = business_serializers.BusinessClientEditSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"
    allowed_methods = ["PATCH",]

    def get_queryset(self):
        return business_models.BusinessClient.objects.all()
    

class BusinessClientDeleteView(generics.DestroyAPIView):
    """
    API view to delete an existing client for a specific business.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = "uid"

    def get_queryset(self):
        return business_models.BusinessClient.objects.all()
    
    def perform_destroy(self, instance):
        if not instance.business.user == self.request.user:
            raise ValidationError(
                _("You are not allowed to delete this client.")
            )
        super().perform_destroy(instance)


class BusinessClientInviteAcceptView(generics.UpdateAPIView):
    """
    API view to accept a client invitation.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = business_serializers.BusinessClientInviteAcceptSerializer
    lookup_field = "uid"
    allowed_methods = ["PATCH",]

    def get_queryset(self):
        return business_models.BusinessClient.objects.all()


class BusinessClientInviteIgnoreView(generics.UpdateAPIView):
    """
    API view to ignore a client invitation.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = business_serializers.BusinessClientInviteIgnoreSerializer
    lookup_field = "uid"
    allowed_methods = ["PATCH",]

    def get_queryset(self):
        return business_models.BusinessClient.objects.all()


class BusinessClientInviteResendView(generics.UpdateAPIView):
    """
    API view to resend a client invitation.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = business_serializers.BusinessClientInviteResendSerializer
    lookup_field = "uid"
    allowed_methods = ["PATCH",]

    def get_queryset(self):
        return business_models.BusinessClient.objects.all()


class BusinessNotificationSettingsView(generics.UpdateAPIView):
    """
    API view to update the notification settings for a specific business.
    """
    serializer_class = business_serializers.BusinessNotificationSettingsSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = ["PATCH",]

    def get_queryset(self):
        return business_models.BusinessNotificationSenderSettings.objects.filter(
            business__uid=self.kwargs.get("business_uid"),
        )

    def get_object(self):
        return self.get_queryset().first()


class BookingHoursMeView(generics.ListAPIView):
    """
    API view to list booking hours for the authenticated user.
    """
    serializer_class = business_serializers.BookingHoursSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_bookings(self, user, start_datetime, end_datetime):
        return business_models.UserBusinesBooking.objects.filter(
            user=user,
            date__gte=start_datetime.date(),
            date__lte=end_datetime.date(),
        )

    def get_queryset(self):
        user = self.request.user
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        step = int(self.request.query_params.get("step", 30))

        if not start_date or not end_date:
            raise ValidationError(
                _("Both start_date and end_date are required.")
            )

        start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        if (end_datetime - start_datetime).days > 7:
            raise ValidationError(
                _("The difference between start_date and end_date should not exceed 7 days.")
            )

        bookings = self.get_bookings(user, start_datetime, end_datetime)
        
        builder = BookingHoursBuilder(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            step=datetime.timedelta(minutes=step),
            bookings=bookings
        )
        
        return builder.build_list()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for booking hours",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for booking hours",
                required=False,
            ),
            OpenApiParameter(
                name="step",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Step in minutes for booking hours",
                required=False,
                default=30,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BookingHoursView(BookingHoursMeView):
    def get_bookings(self, user, start_datetime, end_datetime):
        business_uid = self.kwargs.get("business_uid")
        filter_kwargs = {
            "business__uid": business_uid,
            "date__gte": start_datetime.date(),
            "date__lte": end_datetime.date(),
        }
        employee_uid = self.request.query_params.get("employee_uid", None)
        if employee_uid:
            filter_kwargs["employee__uid"] = employee_uid

        bookings = business_models.UserBusinesBooking.objects.filter(
            **filter_kwargs,
        )
        return bookings

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="employee_uid",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Employee UID to filter booking hours",
                required=False,
            ),
            OpenApiParameter(
                name="start_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="Start date for booking hours",
                required=False,
            ),
            OpenApiParameter(
                name="end_date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description="End date for booking hours",
                required=False,
            ),
            OpenApiParameter(
                name="step",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Step in minutes for booking hours",
                required=False,
                default=30,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


#----------------- TEST NOTIFICATIONS -----------------
class TestNotificationView(generics.GenericAPIView):
    """
    API view to test the notification settings for a specific business.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        celery_app.send_task(
            "send_reminder_notification",
        )
        return Response(status=status.HTTP_200_OK)
    

class TestNotificationDailyView(generics.GenericAPIView):
    """
    API view to test the daily notification settings for a specific business.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        celery_app.send_task(
            "send_reminder_notification_daily",
        )
        return Response(status=status.HTTP_200_OK)


class WorkingHoursBatchUpdateView(generics.CreateAPIView):
    """
    API view to batch update working hours for multiple services.
    """
    serializer_class = business_serializers.WorkingHoursBatchUpdateSerializer
    permission_classes = [IsAuthenticated]

