from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from business import models as business_models
from user import models as user_models
from business import enums as business_enums

from user.geo_utils.serializers import LocationPointDisplaySerializer

from celery import current_app as celery_app
from rating import enums as rating_enums
from rating import models as rating_models

from user import serializers as user_serializers
from notifications.task_sender import NotificationTaskSender


from core.validators import phone_validator


class WorkingHoursEntrySerializer(serializers.Serializer):
    day_of_week = serializers.ChoiceField(choices=business_enums.DayOfWeekChoices.choices)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    visit_type = serializers.ChoiceField(choices=business_enums.VisitTypeChoices.choices, required=False, allow_null=True)


class WorkingHoursBatchUpdateSerializer(serializers.Serializer):

    service_uid = serializers.UUIDField(allow_null=True, required=False, write_only=True)
    employee_uid = serializers.UUIDField(allow_null=True, required=False, write_only=True)
    business_uid = serializers.UUIDField(allow_null=True, required=False, write_only=True)

    working_hours = serializers.ListField(
        child=WorkingHoursEntrySerializer(),
        write_only=True,
        required=True,
    )

    def validate(self, attrs):
        service_uid = attrs.get("service_uid", None)
        employee_uid = attrs.get("employee_uid", None)
        business_uid = attrs.get("business_uid", None)

        if not any([service_uid, employee_uid, business_uid]):
            raise serializers.ValidationError(
                _("At least one of service_uid, employee_uid, or business_uid must be provided.")
            )
        return attrs

    def create(self, validated_data):
        instances = []
        service_uid = validated_data.get("service_uid", None)
        employee_uid = validated_data.get("employee_uid", None)
        business_uid = validated_data.get("business_uid", None)
        working_hours_data = validated_data.get("working_hours", [])

        if service_uid:
            services = business_models.Service.objects.filter(uid=service_uid).all()
            instances.extend(services)
        if employee_uid:
            employees = business_models.Employee.objects.filter(uid=employee_uid).all()
            instances.extend(employees)
        if business_uid:
            businesses = business_models.Business.objects.filter(uid=business_uid).all()
            instances.extend(businesses)
        
        working_hours_objs = []
        for entry in working_hours_data:
            working_hours_objs.append(
                business_models.WorkingHours.objects.update_or_create(
                    visit_type=entry.get("visit_type", None),
                    day_of_week=entry.get("day_of_week"),
                    start_time=entry.get("start_time"),
                    end_time=entry.get("end_time"),
                )[0]
            )
        for instance in instances:
            instance.working_hours.set(working_hours_objs)
            instance.save()

        return instances

        
class BusinessNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = business_models.BusinessNotificationSenderSettings
        fields = (
            "uid",

            "email_notifications",
            "push_notifications",
            
            "booking_email",
            "booking_notification",
            
            "reminder_email",
            "reminder_notification",
        )
        read_only_fields = ["uid",]


class ClientListSerializer(serializers.Serializer):
    uid = serializers.UUIDField()
    avatar = serializers.ImageField()
    avatar_id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()


class ClientListV2Serializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        source="business.uid",
    )
    user = ClientListSerializer(
        read_only=True,
    )
    booking_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )

    class Meta:
        model = business_models.BusinessClient
        fields = [
            "uid",
            "user",
            "business",
            "bio",
            "booking_count",
            "status",
            "created_at",
            "updated_at",
        ]


class BusinessClientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new business client
    """
    business = serializers.UUIDField(
        write_only=True,
    )
    email = serializers.EmailField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    phone = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = business_models.BusinessClient
        fields = [
            "uid",
            "email",
            "phone",
            "business",
            "bio",
        ]
        read_only_fields = ["uid",]

    def validate_business(self, value):
        """
        Validate the business field.
        """
        user = self.context["request"].user
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(
                _("Business with the provided UID does not exist.")
            )
        if not user == business.user:
            raise serializers.ValidationError(
                _("You are not allowed to create a client for this business.")
            )
        return business
    
    def validate_phone(self, value):
        """
        Validate the phone field.
        """
        if value:
            return phone_validator(value)
        return value

    def validate(self, attrs):
        email = attrs.pop("email", None)
        phone = attrs.pop("phone", None)
        if not email and not phone:
            raise serializers.ValidationError(
                _("Either email or phone must be provided.")
            )
        
        client_user = None
        if email and phone:
            client_user = user_models.User.objects.filter(
                email=email,
                phone=phone
            ).first()
        elif email:
            client_user = user_models.User.objects.filter(email=email).first()
        elif phone:
            client_user = user_models.User.objects.filter(phone=phone).first()
            
        if not client_user:
            raise serializers.ValidationError(
                _("User with provided email or phone does not exist.")
            )
        attrs["user"] = client_user
        return attrs

    def create(self, validated_data):
        instance, _ = business_models.BusinessClient.objects.update_or_create(
            user=validated_data["user"],
            business=validated_data["business"],
            defaults={
                "bio": validated_data.get("bio", ""),
                # "status": business_enums.ClientStatusChoices.PENDING.value,
            }
        )
        NotificationTaskSender.send_client_created_notification(
            client=instance,
        )
        return instance
    

class BusinessClientEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = business_models.BusinessClient
        fields = [
            "uid",
            "bio",
        ]
        read_only_fields = ["uid",]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not instance.business.user == user:
            raise serializers.ValidationError(
                _("You are not allowed to edit this client.")
            )
        return super().update(instance, validated_data)


class WorkingHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = business_models.WorkingHours
        fields = [
            "uid",
            "day_of_week",
            "start_time",
            "end_time",
        ]


class SocialMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = business_models.SocialMedia
        fields = [
            "uid",
            "platform",
            "name",
            "url",
        ]


class ServiceSubCategorySerializer(serializers.ModelSerializer):
    
    """
    Serializer for ServiceCategory model.
    """

    class Meta:
        model = business_models.ServiceCategory
        fields = [
            "uid",
            "subcategories_count",
            "name",
            "name_en",
            "name_sq",
            "description",
            "description_en",
            "description_sq",
            "price",
            "currency",
            "currency_symbol",
            "duration",
            "logo",
        ]


class ServiceCategorySerializer(serializers.ModelSerializer):
    
    """
    Serializer for ServiceCategory model.
    """
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    service_type = serializers.ChoiceField(choices=business_enums.ServiceTypeChoices.choices)
    
    class Meta:
        model = business_models.ServiceCategory
        fields = [
            "uid",
            "subcategories",
            "subcategories_count",
            "name",
            "name_en",
            "name_sq",
            "service_type",
            "description",
            "description_en",
            "description_sq",
            "price",
            "currency",
            "currency_symbol",
            "duration",
            "logo",
        ]


class ServiceCategoryDetailSerializer(serializers.ModelSerializer):
    service_type = serializers.ChoiceField(choices=business_enums.ServiceTypeChoices.choices)
    subcategories = ServiceCategorySerializer(many=True, read_only=True)

    class Meta:
        model = business_models.ServiceCategory
        fields = [
            "uid",
            "name",
            "service_type",
            "description",
            "logo",
            "subcategories",
        ]


class GalleryImageSerializer(serializers.ModelSerializer):
    """
    Serializer for GalleryImage model.
    """

    class Meta:
        model = business_models.Gallery
        fields = [
            "uid",
            "image",
        ]

class VideoGallerySerializer(serializers.ModelSerializer):

    class Meta:
        model = business_models.VideoGallery
        fields = [
            "uid",
            "video",
        ]


class BusinessListSerializer(serializers.ModelSerializer):

    location = LocationPointDisplaySerializer(
        read_only=True,
    )
    collaboration_location = LocationPointDisplaySerializer(
        read_only=True,
    )
    category = ServiceCategorySerializer(
        read_only=True,
    )
    categories = ServiceCategorySerializer(
        many=True,
        read_only=True,
    )
    working_hours = WorkingHoursSerializer(
        source="get_real_working_hours",
        many=True,
        read_only=True,
    )
    breaking_hours = WorkingHoursSerializer(
        many=True,
        read_only=True,
    )
    images = GalleryImageSerializer(
        many=True,
        read_only=True,
    )
    videos = VideoGallerySerializer(
        many=True,
        read_only=True,
    )
    socials = SocialMediaSerializer(
        many=True,
        read_only=True,
    )
    average_rating = serializers.FloatField(
        read_only=True,
        default=0.0,
    )
    rating_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )
    is_favorite = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    is_saved = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    distance_to = serializers.CharField(
        read_only=True,
        default=None,
    )
    notification_settings = BusinessNotificationSettingsSerializer(
        read_only=True,
    )
    main_image = GalleryImageSerializer(
        read_only=True,
        default=None,
    )
    class Meta:
        model = business_models.Business
        fields = [
            "uid",
            "business_type",
            "average_rating",
            "is_favorite",
            "is_saved",
            "rating_count",
            "distance_to",
            "name",
            "surname",
            "store_name",
            "collaboration_address",
            "collaboration_location",
            "collaboration_address_on",
            "address",
            "location",
            "address_on",
            "bio",
            "contact_number",
            "note_to_clients",
            "collaborated_business",
            "contact_email",
            "working_hours",
            "breaking_hours",
            "visit_type",
            "category",
            "main_image",
            "categories",
            "images",
            "videos",
            "socials",
            "notification_settings",
            "time_step",
            "apply_for_weeks",
            "apply_for_weeks_date",
            "metadata",
        ]


class BusinessShortListSerializer(BusinessListSerializer):
    """
    Serializer for listing businesses with minimal fields.
    """
    class Meta:
        model = business_models.Business
        fields = [
            "uid",
            "name",
            "store_name",
            "collaboration_address",
            "collaboration_location",
            "address",
            "location",
            "collaboration_address_on",
            "address_on",
            "main_image",
            "working_hours",
            "breaking_hours",
        ]


class BusinessDetailSerializer(BusinessListSerializer):
    rating_stats = serializers.SerializerMethodField()

    def __get_percentage(self,obj, choice: str, total: int) -> float:
        if total == 0:
            return 0
        choice_count = rating_models.Rating.objects.filter(
            business=obj,
            rating=choice.value,
        ).count()
        return (choice_count / total) * 100 if total > 0 else 0
        

    def get_rating_stats(self, obj):

        all_ratings_count = obj.rating_count
        return {
            choice: self.__get_percentage(obj, choice, all_ratings_count)
            for choice in rating_enums.RatingChoices
        }

    class Meta:
        model = business_models.Business
        fields = [
            "uid",
            "business_type",
            "average_rating",
            'rating_stats',
            "is_favorite",
            "is_saved",
            "rating_count",
            "distance_to",
            "name",
            "surname",
            "store_name",
            "collaboration_address",
            "collaboration_location",
            "collaboration_address_on",
            "address",
            "location",
            "address_on",
            "bio",
            "contact_number",
            "note_to_clients",
            "collaborated_business",
            "contact_email",
            "working_hours",
            "breaking_hours",
            "visit_type",
            "category",
            "main_image",
            "categories",
            "images",
            "videos",
            "socials",
            "notification_settings",
            "time_step",
            "apply_for_weeks",
            "apply_for_weeks_date",
            "metadata",
        ]

class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a booking.
    """
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    employee = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    services = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True,
    )
    categories = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    day_of_week = serializers.ChoiceField(
        choices=business_enums.DayOfWeekChoices.choices,
        write_only=True,
        required=True,
    )
    start_time = serializers.TimeField(
        write_only=True,
        required=True,
    )
    end_time = serializers.TimeField(
        write_only=True,
        required=True,
    )
    date = serializers.DateField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = business_models.UserBusinesBooking
        fields = [
            "uid",
            "business",
            "employee",
            "services",
            "categories",
            "start_time",
            "end_time",
            "day_of_week",
            "date",
            "status",
        ]
        read_only_fields = [
            "uid",
            "status",
        ]
    
    def validate_services(self, value):
        """
        Validate the services field.
        """
        services = business_models.Service.objects.filter(
            uid__in=value,
        ).all()
        if not services:
            raise serializers.ValidationError(
                _("Services not found.")
            )
        return services

    def validate_employee(self, value):
        """
        Validate the employee field.
        """
        employee = business_models.Employee.objects.filter(
            uid=value,
        ).first()
        if not employee:
            raise serializers.ValidationError(
                _("Employee not found.")
            )
        return employee

    def validate_business(self, value):
        """
        Validate the business field.
        """
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(
                _("Business not found.")
            )
        return business
    
    def validate_categories(self, value):
        """
        Validate the categories field.
        """
        if not value:
            return []
        categories = business_models.ServiceCategory.objects.filter(
            uid__in=value,
        ).all()
        if not categories:
            raise serializers.ValidationError(
                _("Categories not found.")
            )
        return categories

    def validate(self, attrs):
        employee = attrs.get("employee", None)
        services = attrs.get("services", [])
        
        if employee and services:
            services_uids = [service.uid for service in services]
            employee_services = employee.services.all()
            if not employee_services.filter(uid__in=services_uids).exists():
                raise serializers.ValidationError(
                    _("Employee does not provide the selected services.")
                )
            
        user = self.context["request"].user
        attrs["user"] = user
        return super().validate(attrs)
    
    def create(self, validated_data):
        validated_data.update({
            "status": business_enums.BookingStatusChoices.CONFIRMED.value,
        })
        instance: business_models.UserBusinesBooking = super().create(validated_data)
        instance.update_or_create_client()
        celery_app.send_task(
            "send_booked_notification",
            kwargs={
                "booking_uid": str(instance.uid),
            },
        )
        celery_app.send_task(
            "send_booked_mail",
            kwargs={
                "booking_uid": str(instance.uid),
            },
        )
        return instance


class BookingAddSerializer(BookingCreateSerializer):

    client_uid = serializers.UUIDField(
        write_only=True,
        required=True,
    )

    def validate(self, attrs):
        client_uid = attrs.pop("client_uid", None)
        client_user = user_models.User.objects.filter(
            uid=client_uid,
        ).first()
        if not client_user:
            raise serializers.ValidationError(
                _("Client user not found.")
            )
        attrs["user"] = client_user

        return attrs

    class Meta:
        model = business_models.UserBusinesBooking
        fields = [
            "uid",
            "client_uid",
            "business",
            "employee",
            "services",
            "start_time",
            "end_time",
            "day_of_week",
            "date",
            "status",
        ]
        read_only_fields = [
            "uid",
            "status",
        ]


class BookingEditSerializer(BookingCreateSerializer):

    client_uid = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    class Meta:
        model = business_models.UserBusinesBooking
        fields = [
            "uid",
            "client_uid",
            "employee",
            "services",
            "start_time",
            "end_time",
            "day_of_week",
            "date",
            "status",
            "cancel_reason",
        ]
        read_only_fields = [
            "uid",
        ]
    
    def validate_status(self, value):
        user = self.context["request"].user
        if user not in [
            self.instance.user,
            self.instance.business.user,
        ]:
            raise serializers.ValidationError(
                _("You cannot change the status of the booking.")
            )
        
        return value
    
    def validate(self, attrs):
        client_uid = attrs.pop("client_uid", None)
        if client_uid:
            client_user = user_models.User.objects.filter(
                uid=client_uid,
            ).first()
            if not client_user:
                raise serializers.ValidationError(
                    _("Client user not found.")
                )
            attrs['user'] = client_user
        return attrs
            
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # if the booking is cancled send PN and mail
        if instance.status == business_enums.BookingStatusChoices.CANCELLED:
            celery_app.send_task(
                "send_canceled_notification",
                kwargs={
                    "booking_uid": str(instance.uid),
                },
            )
            celery_app.send_task(
                "send_canceled_mail",
                kwargs={
                    "booking_uid": str(instance.uid),
                },
            )
        else:
            celery_app.send_task(
                "send_booking_updated_notification",
                kwargs={
                    "booking_uid": str(instance.uid),
                },
            )
            celery_app.send_task(
                "send_booking_updated_mail",
                kwargs={
                    "booking_uid": str(instance.uid),
                },
            )
        return instance
    

class ServiceListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing services.
    """
    business = BusinessShortListSerializer(
        read_only=True,
    )
    category = ServiceCategorySerializer(
        read_only=True,
    )
    categories = ServiceCategorySerializer(
        many=True,
        read_only=True,
    )
    images = GalleryImageSerializer(
        many=True,
        read_only=True,
    )
    working_hours = WorkingHoursSerializer(
        many=True,
        read_only=True,
    )
    average_rating = serializers.FloatField(
        read_only=True,
        default=0.0,
    )
    rating_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )

    class Meta:
        model = business_models.Service
        fields = [
            "uid",
            "name",
            "image",
            "gender",
            "price",
            "currency",
            "currency_symbol",
            "duration",
            "average_rating",
            "rating_count",
            "category",
            "categories",
            "business",
            "images",
            "working_hours",
        ]


class ServiceListInlineSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer()
    
    class Meta:
        model = business_models.Service
        fields = [
            "uid",
            "name",
            "image",
            "price",
            "currency",
            "currency_symbol",
            "duration",
            "created_at",
            "category",
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing employees.
    """
    business = serializers.UUIDField(
        source="business.uid",
        read_only=True,
    )
    user = serializers.UUIDField(
        source="user.uid",
        read_only=True,
    )
    services = ServiceListSerializer(
        many=True,
        read_only=True,
    )
    avatar = serializers.ImageField(
        read_only=True,
    )
    average_rating = serializers.FloatField(
        read_only=True,
        default=0.0,
    )
    working_hours = WorkingHoursSerializer(
        many=True,
        read_only=True,
    )
    free_hours = serializers.DurationField(
        read_only=True,
        default=0.0,
    )
    is_favorite = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    booking_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )
    class Meta:
        model = business_models.Employee
        fields = [
            "uid",
            "name",
            "business",
            "services",
            "user",
            "avatar",
            "average_rating",
            "working_hours",
            "free_hours",
            "is_favorite",
            "booking_count",
            "created_at",
            "updated_at",
        ]


class EmployeeInlineSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(
        source="user.avatar",
        read_only=True,
        default=None,
    )
    class Meta:
        model = business_models.Employee
        fields = [
            "uid",
            "name",
            "avatar",
        ]
    

class BookingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing bookings.
    """
    user = user_serializers.userInlineDetailsSerializer(
        read_only=True,
    )
    business = serializers.UUIDField(
        source="business.uid",
        read_only=True,
    )
    main_image = GalleryImageSerializer(
        source="business.main_image",
        read_only=True,
        default=None,
    )
    employee = EmployeeInlineSerializer(
        read_only=True,
    )
    services = ServiceListInlineSerializer(
        many=True,
        read_only=True,
    )
    categories = ServiceCategorySerializer(
        many=True,
        read_only=True,
    )
    rating_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )
    business_rating_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )
    is_booking_rated = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    is_business_rated = serializers.BooleanField(
        read_only=True,
        default=False,
    )

    class Meta:
        model = business_models.UserBusinesBooking
        fields = [
            "uid",
            "user",
            "business",
            "main_image",
            "employee",
            "services",
            "categories",
            "start_time",
            "end_time",
            "day_of_week",
            "date",
            "status",
            "cancel_reason",
            "rating_count",
            "business_rating_count",
            "is_booking_rated",
            "is_business_rated",
            "visit_type",
            "created_at",
            "updated_at",
        ]

class ServiceAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for service availability data.
    """
    date = serializers.DateField()
    day_of_week = serializers.ChoiceField(choices=business_enums.DayOfWeekChoices.choices)
    available_slots = serializers.ListField(
        child=serializers.DictField(
            child=serializers.TimeField()
        )
    )
    booked_slots = serializers.ListField(
        child=serializers.DictField(
            child=serializers.TimeField()
        )
    )


class SearchListSerializer(serializers.Serializer):

    DATA_TYPE_MAP = {
        business_models.UserBusinesBooking: business_enums.SearchDataTypeChoices.BOOKING.value,
        business_models.Employee: business_enums.SearchDataTypeChoices.EMPLOYEE.value,
        user_models.User: business_enums.SearchDataTypeChoices.CLIENT.value,
    }
    
    data_type = serializers.SerializerMethodField()
    uid = serializers.UUIDField(
        read_only=True,
        default=None,
    )
    avatar = serializers.ImageField(
        read_only=True,
        default=None,
    )
    name = serializers.CharField(
        read_only=True,
        default=None,
    )
    user = user_serializers.userInlineDetailsSerializer(
        read_only=True,
        default=None,
    )
    employee = EmployeeInlineSerializer(
        read_only=True,
        default=None,
    )
    average_rating = serializers.FloatField(
        read_only=True,
        default=None,
    )
    services = ServiceListInlineSerializer(
        many=True,
        read_only=True,
        default=None,
    )
    start_time = serializers.TimeField(
        read_only=True,
        default=None,
    )
    end_time = serializers.TimeField(
        read_only=True,
        default=None,
    )
    day_of_week = serializers.CharField(
        read_only=True,
        default=None,
    )
    date = serializers.DateField(
        read_only=True,
        default=None,
    )
    visit_type = serializers.CharField(
        read_only=True,
        default=None,
    )
    status = serializers.CharField(
        read_only=True,
        default=None,
    )

    def get_data_type(self, obj):
        return self.DATA_TYPE_MAP.get(type(obj), "unknown")
    

class ServicesSearchListSerializer(serializers.Serializer):

    DATA_TYPE_MAP = {
        business_models.Business: business_enums.SearchDataTypeChoices.BUSINESS.value,
        business_models.Service: business_enums.SearchDataTypeChoices.SERVICE.value,
    }

    data_type = serializers.SerializerMethodField()
    uid = serializers.UUIDField(
        read_only=True,
        default=None,
    )
    business = BusinessShortListSerializer(
        read_only=True,
        default=None,
    )
    images = GalleryImageSerializer(
        many=True,
        read_only=True,
        default=None,
    )
    main_image = GalleryImageSerializer(
        read_only=True,
        default=None,
    )
    name = serializers.CharField(
        read_only=True,
        default=None,
    )
    store_name = serializers.CharField(
        read_only=True,
        default=None,
    )
    collaboration_address = serializers.CharField(
        read_only=True,
        default=None,
    )
    collaboration_location = LocationPointDisplaySerializer(
        read_only=True,
        default=None,
    )
    collaboration_address_on = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    address = serializers.CharField(
        read_only=True,
        default=None,
    )
    location = LocationPointDisplaySerializer(
        read_only=True,
        default=None,
    )
    address_on = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    working_hours = WorkingHoursSerializer(
        many=True,
        read_only=True,
    )
    breaking_hours = WorkingHoursSerializer(
        many=True,
        read_only=True,
    )
    is_favorite = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    is_saved = serializers.BooleanField(
        read_only=True,
        default=False,
    )

    def get_data_type(self, obj):
        return self.DATA_TYPE_MAP.get(type(obj), "unknown")

class BookingHoursSerializer(serializers.Serializer):
    """
    Serializer for booking hours.
    """
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_booked = serializers.BooleanField(default=False)
    bookings_uids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=None,
    )
    user_uids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=None,
    )


class BusinessClientInviteAcceptSerializer(serializers.ModelSerializer):
    """
    Serializer for accepting a business client invitation.
    """
    class Meta:
        model = business_models.BusinessClient
        fields = [
            "uid",
            "status",
        ]
        read_only_fields = ["uid", "status"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not instance.user == user:
            raise serializers.ValidationError(
                _("You are not allowed to accept this invitation.")
            )
        
        instance.status = business_enums.ClientStatusChoices.ACCEPTED.value
        instance.save(
            update_fields=["status"]
        )
        return instance
    

class BusinessClientInviteIgnoreSerializer(serializers.ModelSerializer):
    """
    Serializer for ignoring a business client invitation.
    """
    class Meta:
        model = business_models.BusinessClient
        fields = [
            "uid",
            "status",
        ]
        read_only_fields = ["uid", "status"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not instance.user == user:
            raise serializers.ValidationError(
                _("You are not allowed to ignore this invitation.")
            )
        
        instance.status = business_enums.ClientStatusChoices.REJECTED.value
        instance.save(
            update_fields=["status"]
        )
        return instance
    

class BusinessClientInviteResendSerializer(serializers.ModelSerializer):
    """
    Serializer for resending a business client invitation.
    """
    class Meta:
        model = business_models.BusinessClient
        fields = [
            "uid",
        ]
        read_only_fields = ["uid"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not instance.business.user == user:
            raise serializers.ValidationError(
                _("You are not allowed to resend this invitation.")
            )
        
        NotificationTaskSender.send_client_invitation_notification(
            client=instance,
        )
        instance.status = business_enums.ClientStatusChoices.PENDING.value
        instance.save(
            update_fields=["status"]
        )
        
        return instance

