from typing import Optional

from django.db import models
from django.db.models import OuterRef, Subquery, Avg, Count, Exists, BooleanField, Value
from django.db.models import (
    Sum,
    ExpressionWrapper,
    F,
    DurationField,
    FloatField,
    Case,
    When,
    Func,
)
from django.db.models.functions import Coalesce, Cast, Extract
from datetime import timedelta

from user import models as user_models
from onboarding import models as onboarding_models
from rating import models as rating_models
from business import models as business_models
from user import models as user_models



class ExtractTotalSeconds(Func):
    """Custom function to extract total seconds from an interval in Postgres."""
    function = 'EXTRACT'
    template = "%(function)s(EPOCH FROM %(expressions)s)"
    output_field = FloatField()


class ServiceRegistry:

    @classmethod
    def get_annotated_services(
        cls,
        user: Optional[user_models.User] = None,
    ) -> models.QuerySet:
        """
        Fetch all services with annotations:
            - average_rating: Average rating aggregated from bookings containing this service.
            - rating_count: Total number of ratings linked via bookings containing this service.
            - is_favorite: (placeholder, always False – no service favorite model present).
            - is_saved: (placeholder, always False – no service save model present).
        """
        # Aggregate ratings through bookings that include this service.
        # Path: Service -> service_bookings (M2M reverse) -> ratings (FK on Rating.booking)
        qs = (
            business_models.Service.objects.all()
            .annotate(
                average_rating=Coalesce(
                    Avg("service_bookings__ratings__rating"),
                    Value(0.0),
                    output_field=FloatField(),
                ),
                rating_count=Count("service_bookings__ratings", distinct=True),
            )
            .prefetch_related(
                "business",
                "categories",
                "images",
                "working_hours",
            )
            .distinct()
        )
        return qs


class BusinessRegistry:

    @classmethod
    def get_annotated_business(
        cls,
        user: Optional[user_models.User] = None
    ) -> models.QuerySet:
        """
        Fetch all businesses with annotations:
            - average_rating: Average rating of the business.
            - rating_count: Total number of ratings for the business.
            - is_favorite: Whether the business is marked as favorite by the user.
            - is_saved: Whether the business is saved by the user.
        """

        avg_rating_subquery = rating_models.Rating.objects.filter(
            business=OuterRef("pk")
        ).values("business").annotate(
            avg=models.Avg("rating")
        ).values("avg")[:1]

        qs = (
            business_models.Business.objects.all()
            .annotate(
                average_rating=Coalesce(
                    Subquery(avg_rating_subquery),
                    Value(0.0),
                    output_field=FloatField()
                ),
                rating_count=Count("ratings"),
            )
            .prefetch_related(
                "categories",
                "images",
                "videos",
                "working_hours",
                "user",
                "ratings",
                "notification_settings",
            )
            .distinct()
        )

        if user:
            favorite_exists = rating_models.UserBusinessFavorite.objects.filter(
                user=user, business=OuterRef("pk")
            )
            saved_exists = rating_models.UserBusinessSave.objects.filter(
                user=user, business=OuterRef("pk")
            )

            qs = qs.annotate(
                is_favorite=Exists(favorite_exists),
                is_saved=Exists(saved_exists),
            )
        else:
            # Set defaults if no user is provided
            qs = qs.annotate(
                is_favorite=Value(False, output_field=BooleanField()),
                is_saved=Value(False, output_field=BooleanField()),
            )

        return qs
    
    @classmethod
    def get_annotated_business_clients(
        cls, 
        business_uid: str,
    ):
        """
            Return list of users that had a booking with this business.
            - booking_count: Number of bookings the user has with this business.
        """
        # Get all users who have bookings with this business
        clients = (
            user_models.User.objects.filter(
                user_bookings__business__uid=business_uid
            )
            .annotate(
                booking_count=Count('user_bookings', filter=models.Q(user_bookings__business__uid=business_uid))
            )
            .prefetch_related(
                'user_bookings',
                'user_bookings__services',
                'user_bookings__employee'
            )
            .distinct()
        )

        return clients
    

class EmployeeRegistry:

    @classmethod
    def get_annotated_employees(
        cls,
        user: Optional[user_models.User] = None,
    ) -> models.QuerySet:
        """
        Fetch all employees with their annotations:
            - average_rating: Average rating of the employee.
            - working_days_count: Number of distinct days the employee works.
            - booked_days_count: Number of distinct days the employee is booked.
            - free_hours: The remaining available hours (working hours minus booked hours).
            - is_favorite: Whether the employee is marked as favorite by the user.
        """
        avg_rating_subquery = rating_models.Rating.objects.filter(
            employee=OuterRef("pk")
        ).values("employee").annotate(
            avg=Avg("rating")
        ).values("avg")[:1]

        employees_qs = (
            business_models.Employee.objects.all()
            .annotate(
                working_days_count=Count('working_hours__day_of_week', distinct=True),
                booked_days_count=Count('employee_bookings__day_of_week', distinct=True),
                working_duration=Sum(
                    ExpressionWrapper(
                        F("working_hours__end_time") - F("working_hours__start_time"),
                        output_field=DurationField(),
                    )
                ),
                total_working_hours=Coalesce(
                    F("working_duration"),
                    timedelta(0),
                ),
                total_booked_hours=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("employee_bookings__end_time") - F("employee_bookings__start_time"),
                            output_field=DurationField(),
                        )
                    ),
                    timedelta(0),
                ),
                free_hours=ExpressionWrapper(
                    F("total_working_hours") - F("total_booked_hours"),
                    output_field=DurationField(),
                ),
                average_rating=Coalesce(
                    Subquery(avg_rating_subquery),
                    Value(0.0),
                    output_field=FloatField()
                ),
            )
            .prefetch_related(
                "business",
                "user",
                "ratings",
            )
            .distinct()
        )

        if user:
            favorite_exists = rating_models.UserEmployeeFavorite.objects.filter(
                user=user, employee=OuterRef("pk")
            )

            employees_qs = employees_qs.annotate(
                is_favorite=Exists(favorite_exists),
            )
        else:
            employees_qs = employees_qs.annotate(
                is_favorite=Value(False, output_field=BooleanField()),
            )

        employees_qs = employees_qs.annotate(
            booking_count=Count(
                'employee_bookings',
                distinct=True,
            )
        )
        return employees_qs


class ClientRegistry:

    @classmethod
    def get_annotated_clients(
        cls,
        business_uid: str,
    ) -> models.QuerySet:
        """
        Fetch all clients with their annotations:
            - booking_count: Total number of bookings made by the client.
        """

        clients_qs = (
            business_models.BusinessClient.objects.all()
            .annotate(
                booking_count=Count(
                    'user__user_bookings',
                    distinct=True,
                    filter=models.Q(user__user_bookings__business__uid=business_uid),
                )
            )
        )

        return clients_qs

