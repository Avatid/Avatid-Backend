from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from onboarding import models as onboarding_models
from onboarding import enums as onboarding_enums
from business import models as business_models
from business import serializers as business_serializers
from business import enums as business_enums

from user.geo_utils.main import GeoUtils
from user.geo_utils.serializers import LocationPointDisplaySerializer

from onboarding import utils as onboarding_utils

from celery import current_app as celery_app
from user.enums import UserRoleChoices



class BusinessCreateSerializer(serializers.ModelSerializer):
    location = LocationPointDisplaySerializer(required=False, write_only=True, allow_null=True)
    collaboration_location = LocationPointDisplaySerializer(required=False, write_only=True, allow_null=True)
    category = serializers.UUIDField(
        write_only=True,
        required=False,
    )
    categories = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )
    class Meta:
        model = business_models.Business
        fields = [
            "uid",
            "business_type",
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
            "visit_type",
            "category",
            "categories",
            "contact_number",
            "contact_email",
            "note_to_clients",
            "collaborated_business",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate_location(self, value: dict):
        if value:
            return GeoUtils.dict_to_point(value)
        return None
    
    def validate_collaboration_location(self, value: dict):
        if value:
            return GeoUtils.dict_to_point(value)
        return None
    
    def validate_category(self, value):
        category = business_models.ServiceCategory.objects.filter(
            uid=value,
        ).first()
        if not category:
            raise serializers.ValidationError(_("Invalid category."))
        return category
    
    def validate_categories(self, value):
        categories = business_models.ServiceCategory.objects.filter(
            uid__in=value,
        )
        if not categories.exists():
            raise serializers.ValidationError(_("Invalid categories."))
        return categories
    
    def validate(self, attrs):
        user = self.context["request"].user
        if business_models.Business.objects.filter(
            user=user,
        ).exists():
            raise serializers.ValidationError(_("You already have a business."))
        attrs["user"] = user
        return super().validate(attrs)
    
    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        sub_categories = business_models.ServiceCategory.objects.filter(
            parent__in=categories,
        )
        instance = super().create(validated_data)
        sub_main_categories = business_models.ServiceCategory.objects.filter(
            parent=instance.category,
        )
        if categories:
            instance.categories.set(categories)
        if sub_categories.exists():
            instance.categories.add(*sub_categories)
        if sub_main_categories.exists():
            instance.categories.add(*sub_main_categories)
        return instance
    

class BusinessUpdateSerializer(serializers.ModelSerializer):
    location = LocationPointDisplaySerializer(required=False, write_only=True, allow_null=True)
    collaboration_location = LocationPointDisplaySerializer(required=False, write_only=True, allow_null=True)
    category = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    categories = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    class Meta:
        model = business_models.Business
        fields = [
            "uid",
            "business_type",
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
            "visit_type",
            "category",
            "categories",
            "contact_number",
            "contact_email",
            "note_to_clients",
            "collaborated_business",
            "time_step",
            "apply_for_weeks",
            "apply_for_weeks_date",
            "metadata",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate_location(self, value: dict):
        if value:
            return GeoUtils.dict_to_point(value)
        return None
    
    def validate_collaboration_location(self, value: dict):
        if value:
            return GeoUtils.dict_to_point(value)
        return None
    
    def validate_category(self, value):
        category = business_models.ServiceCategory.objects.filter(
            uid=value,
        ).first()
        if not category:
            raise serializers.ValidationError(_("Invalid category."))
        return category
    
    def validate_categories(self, value):
        categories = business_models.ServiceCategory.objects.filter(
            uid__in=value,
        )
        if not categories.exists():
            raise serializers.ValidationError(_("Invalid categories."))
        return categories
    
    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        return super().validate(attrs)
    
    def update(self, instance, validated_data):
        old_sub_main_categories = business_models.ServiceCategory.objects.filter(
            parent=instance.category,
        )
        categories = validated_data.pop("categories", [])
        sub_categories = business_models.ServiceCategory.objects.filter(
            parent__in=categories,
        )
        instance = super().update(instance, validated_data)
        sub_main_categories = business_models.ServiceCategory.objects.filter(
            parent=instance.category,
        )
        if not categories:
            categories = instance.categories.all()
        
        categories = list(categories) + list(sub_categories) + list(sub_main_categories)
        instance.categories.set(categories)
        if old_sub_main_categories.exists():
            instance.categories.remove(*old_sub_main_categories)
        return instance


class WorkingHoursCreateSerializer(serializers.ModelSerializer):
    business_uid = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    class Meta:
        model = business_models.WorkingHours
        fields = [
            "uid",
            "business_uid",
            "day_of_week",
            "start_time",
            "end_time",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        business_uid = attrs.pop("business_uid", None)
        business = business_models.Business.objects.filter(
            uid=business_uid,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        attrs["business"] = business
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        business = validated_data.pop("business", None)

        day = validated_data["day_of_week"]
        start = validated_data["start_time"]
        end = validated_data["end_time"]

        instance = business_models.WorkingHours.objects.filter(
            day_of_week=day,
            start_time=start,
            end_time=end,
        ).first()

        if instance is None:
            instance = business_models.WorkingHours.objects.create(
                day_of_week=day,
                start_time=start,
                end_time=end,
            )

        business.working_hours.add(instance)
        return instance
    

class BreakingHoursCreateSerializer(WorkingHoursCreateSerializer):
    def create(self, validated_data):
        business = validated_data.pop("business", None)

        day = validated_data["day_of_week"]
        start = validated_data["start_time"]
        end = validated_data["end_time"]

        instance = business_models.WorkingHours.objects.filter(
            day_of_week=day,
            start_time=start,
            end_time=end,
        ).first()

        if instance is None:
            instance = business_models.WorkingHours.objects.create(
                day_of_week=day,
                start_time=start,
                end_time=end,
            )

        business.breaking_hours.add(instance)
        return instance
    

class WorkingHoursDeleteSerializer(serializers.ModelSerializer):
    business_uid = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    employee_uid = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    working_hours_uid = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    details = serializers.CharField(
        read_only=True,
    )
    class Meta:
        model = business_models.WorkingHours
        fields = [
            "working_hours_uid",
            "business_uid",
            "employee_uid",
            "details",
        ]
        read_only_fields = [
            "details",
        ]

    def validate(self, attrs):
        return attrs
    
    def create(self, validated_data):
        working_hours_uid = validated_data.pop("working_hours_uid", None)
        business_uid = validated_data.pop("business_uid", None)
        employee_uid = validated_data.pop("employee_uid", None)
        working_hours = business_models.WorkingHours.objects.filter(
            uid=working_hours_uid,
        ).first()

        if not working_hours:
            raise serializers.ValidationError(_("Invalid working hours uid."))
        if not business_uid and not employee_uid:
            raise serializers.ValidationError(_("You must provide either business_uid or employee_uid."))
        
        if business_uid:
            business = business_models.Business.objects.filter(
                uid=business_uid,
            ).first()
            if not business:
                raise serializers.ValidationError(_("Invalid business uid."))
            if not business.working_hours.filter(uid=working_hours_uid).exists():
                return {
                    "details": "Working hours not found in business.",
                }
            business.working_hours.remove(working_hours)
            return {
                "details": "Working hours removed from business.",
            }
        
        if employee_uid:
            employee = business_models.Employee.objects.filter(
                uid=employee_uid,
            ).first()
            if not employee:
                raise serializers.ValidationError(_("Invalid employee uid."))
            if not employee.working_hours.filter(uid=working_hours_uid).exists():
                return {
                    "details": "Working hours not found in employee.",
                }
            employee.working_hours.remove(working_hours)
            return {
                "details": "Working hours removed from employee.",
            }
        

class BreakingHoursDeleteSerializer(WorkingHoursDeleteSerializer):

    class Meta:
        model = business_models.WorkingHours
        fields = [
            "working_hours_uid",
            "business_uid",
            "details",
        ]
        read_only_fields = [
            "details",
        ]

    def create(self, validated_data):
        working_hours_uid = validated_data.pop("working_hours_uid", None)
        business_uid = validated_data.pop("business_uid", None)
        working_hours = business_models.WorkingHours.objects.filter(
            uid=working_hours_uid,
        ).first()

        if not working_hours:
            raise serializers.ValidationError(_("Invalid working hours uid."))
        if not business_uid:
            raise serializers.ValidationError(_("You must provide either business_uid or employee_uid."))
        
        business = business_models.Business.objects.filter(
            uid=business_uid,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        if not business.breaking_hours.filter(uid=working_hours_uid).exists():
            return {
                "details": "Working hours not found in business.",
            }
        business.breaking_hours.remove(working_hours)
        return {
            "details": "Working hours removed from business.",
        }     


class SocialCreateSerializer(serializers.ModelSerializer):
    business_uid = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    class Meta:
        model = business_models.SocialMedia
        fields = [
            "uid",
            "business_uid",
            "platform",
            "url",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        business_uid = attrs.pop("business_uid", None)
        business = business_models.Business.objects.filter(
            uid=business_uid,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        attrs["business"] = business
        return attrs
    
    def create(self, validated_data):
        business = validated_data.pop("business", None)
        
        social = business.socials.filter(
            platform=validated_data["platform"],
        ).first()
        if social:
            social.url = validated_data["url"]
            social.save()
            return social
        
        instance = super().create(validated_data)
        business.socials.add(instance)
        return instance


class CostumerCreateSerializer(serializers.ModelSerializer):
    services_interested = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
    )
    uid = serializers.UUIDField(
        read_only=True,
    )

    class Meta:
        model = onboarding_models.Costumer
        fields = [
            "services_interested",
            "routine_data",
            "gender",
            "name",
            "surname",
            "uid",
        ]

    def validate_services_interested(self, value):
        services_interested = business_models.ServiceCategory.objects.filter(
            uid__in=value,
        )
        return services_interested

    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        return super().validate(attrs)
    
    def create(self, validated_data):
        user = validated_data.get("user", None)
        if onboarding_models.Costumer.objects.filter(
            user=user,
        ).exists():
            raise serializers.ValidationError(_("You already have a costumer profile."))
        return super().create(validated_data)


class CostumerDetailSerializer(serializers.ModelSerializer):
    services_interested = business_serializers.ServiceCategorySerializer(
        many=True,
        read_only=True,
    )
    user_uid = serializers.UUIDField(
        source="user.uid",
        read_only=True,
    )
    freelancer_uid = serializers.UUIDField(
        source="user.freelancer.uid",
        read_only=True,
    )
    uid = serializers.UUIDField(
        read_only=True,
    )

    class Meta:
        model = onboarding_models.Costumer
        fields = [
            "uid",
            "user_uid",
            "freelancer_uid",
            "services_interested",
            "routine_data",
            "gender",
            "name",
            "surname",
        ]

class CostumerUpdateSerializer(CostumerCreateSerializer):

    class Meta:
        model = onboarding_models.Costumer
        fields = [
            "services_interested",
            "routine_data",
            "uid",
            "gender",
            "name",
            "surname",
        ]

    def update(self, instance, validated_data):
        services_interested = validated_data.pop("services_interested", [])
        instance = super().update(instance, validated_data)
        if services_interested:
            instance.services_interested.set(services_interested)
        return instance


class UploadImageSerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    
    class Meta:
        model = business_models.Gallery
        fields = [
            "business",
            "name",
            "image",
            "is_main",
        ]

    def validate_business(self, value):
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        user = self.context["request"].user
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return business
    
    def create(self, validated_data):
        business = validated_data.pop("business", None)
        instace = super().create(validated_data)
        business.images.add(instace)
        # update all old images to be not main if the new one is main
        if instace.is_main:
            business.images.exclude(uid=instace.uid).update(is_main=False)
        return instace
    

class UploadVideoSerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    
    class Meta:
        model = business_models.VideoGallery
        fields = [
            "business",
            "name",
            "video",
        ]

    def validate_business(self, value):
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        user = self.context["request"].user
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return business
    
    def create(self, validated_data):
        business = validated_data.pop("business", None)
        instace = super().create(validated_data)
        business.videos.add(instace)
        return instace
    

class ServiceCreateSerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    category = serializers.UUIDField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    categories = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )
    class Meta:
        model = business_models.Service
        fields = [
            "uid",
            "name",
            "image",
            "gender",
            "business",
            "category",
            "categories",
            "duration",
            "price",
            "currency",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate(self, attrs):
        business = business_models.Business.objects.filter(
            uid=attrs.get("business"),
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        
        category = business_models.ServiceCategory.objects.filter(
            uid=attrs.get("category"),
        ).first()
        if not category and not attrs.get("categories"):
            raise serializers.ValidationError(_("You must provide a category or categories."))
        user = self.context["request"].user
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        attrs["business"] = business
        attrs["category"] = category if category else None
        return attrs

    def create(self, validated_data):
        categories_uids = validated_data.pop("categories", [])
        instance = super().create(validated_data)
        if categories_uids:
            categories = business_models.ServiceCategory.objects.filter(
                uid__in=categories_uids,
            )
            instance.categories.set(categories)
            instance.business.categories.add(*categories)
        instance.save()
        return instance


class ServiceUpdateSerializer(ServiceCreateSerializer):
    class Meta:
        model = business_models.Service
        fields = [
            "uid",
            "name",
            "image",
            "gender",
            "category",
            "categories",
            "duration",
            "price",
            "currency",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate(self, attrs):
        category = business_models.ServiceCategory.objects.filter(
            uid=attrs.get("category"),
        ).first()
        if not category and not attrs.get("categories"):
            raise serializers.ValidationError(_("You must provide a category or categories."))
        attrs["category"] = category if category else None
        return attrs

    def update(self, instance, validated_data):
        categories_uids = validated_data.pop("categories", [])
        instance = super().update(instance, validated_data)
        if categories_uids:
            categories = business_models.ServiceCategory.objects.filter(
                uid__in=categories_uids,
            )
            instance.categories.set(categories)
            instance.business.categories.add(*categories)

        instance.save()
        return instance


class UploadImageServiceSerializer(serializers.ModelSerializer):
    service = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    
    class Meta:
        model = business_models.Gallery
        fields = [
            "service",
            "name",
            "image",
        ]

    def validate_service(self, value):
        service = business_models.Service.objects.filter(
            uid=value,
        ).first()
        if not service:
            raise serializers.ValidationError(_("Invalid service uid."))
        user = self.context["request"].user
        if not user == service.business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return service
    
    def create(self, validated_data):
        service = validated_data.pop("service", None)
        instace = super().create(validated_data)
        service.images.add(instace)
        return instace


class WorkingHoursCreateServiceSerializer(serializers.ModelSerializer):
    service = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    class Meta:
        model = business_models.WorkingHours
        fields = [
            "uid",
            "service",
            "day_of_week",
            "start_time",
            "end_time",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate_service(self, value):
        service = business_models.Service.objects.filter(
            uid=value,
        ).first()
        if not service:
            raise serializers.ValidationError(_("Invalid service uid."))
        user = self.context["request"].user
        if not user == service.business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return service

    def create(self, validated_data):
        service = validated_data.pop("service", None)

        day = validated_data["day_of_week"]
        start = validated_data["start_time"]
        end = validated_data["end_time"]

        instance = business_models.WorkingHours.objects.filter(
            day_of_week=day,
            start_time=start,
            end_time=end,
        ).first()

        if instance is None:
            instance = business_models.WorkingHours.objects.create(
                day_of_week=day,
                start_time=start,
                end_time=end,
            )

        service.working_hours.add(instance)
        return instance


class EmployeeCreateSerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    services = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )
    class Meta:
        model = business_models.Employee
        fields = [
            "uid",
            "business",
            "services",
            "name",
            "avatar",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate_services(self, value):
        services = business_models.Service.objects.filter(
            uid__in=value,
        )
        if not services.exists():
            raise serializers.ValidationError(_("Invalid services."))
        return services

    def validate_business(self, value):
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        user = self.context["request"].user
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        if business.business_type == business_enums.BusinessTypeChoices.FREELANCE:
            raise serializers.ValidationError(_("You cannot add employees to a freelancer business."))
        return business
    
    def create(self, validated_data):
        services = validated_data.pop("services", [])
        instance = super().create(validated_data)
        if services:
            instance.services.set(services)
        return instance


class FreelancerToEmployeeSerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    freelancer = serializers.UUIDField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = business_models.Employee
        fields = [
            "uid",
            "business",
            "freelancer",
        ]
        read_only_fields = [
            "uid",
        ]
    
    def validate_business(self, value):
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        user = self.context["request"].user
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return business
    
    def validate_freelancer(self, value):
        freelancer = onboarding_models.FreeLancer.objects.filter(
            uid=value,
        ).first()
        if not freelancer:
            raise serializers.ValidationError(_("Invalid freelancer uid."))
        return freelancer
    
    
    def create(self, validated_data):
        business = validated_data.pop("business", None)
        freelancer = validated_data.pop("freelancer", None)
        return onboarding_utils.add_freelancer_to_employee(freelancer, business)
    

class FreelancerApplySerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    class Meta:
        model = onboarding_models.FreelancerBusinessApply
        fields = [
            "business",
            "uid",
            "status",
        ]
        read_only_fields = [
            "uid",
            "status",
        ]

    def validate_business(self, value):
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        if business.business_type == business_enums.BusinessTypeChoices.FREELANCE:
            raise serializers.ValidationError(_("You cannot apply to a freelancer business."))
        return business
    
    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        return super().validate(attrs)

    def create(self, validated_data):
        user = validated_data.pop("user", None)
        business = validated_data.pop("business", None)
        freelancer = onboarding_models.FreeLancer.objects.filter(
            user=user,
        ).first()
        if not freelancer:
            raise serializers.ValidationError(_("You are not a freelancer."))
        if onboarding_models.FreelancerBusinessApply.objects.filter(
            freelancer=freelancer,
            business=business,
        ).exists():
            raise serializers.ValidationError(_("You already have an application for this business."))
        instance = onboarding_models.FreelancerBusinessApply.objects.create(
            freelancer=freelancer,
            business=business,
        )
        celery_app.send_task(
            "send_apply_notification",
            args=[instance.uid],
        )
        celery_app.send_task(
            "send_apply_email",
            args=[instance.uid],
        )
        return instance


class FreelancerApplyUpdateSerializer(serializers.ModelSerializer):
    business_uid = serializers.UUIDField(
        source="business.uid",
        read_only=True,
    )
    freelancer_uid = serializers.UUIDField(
        source="freelancer.uid",
        read_only=True,
    )
    class Meta:
        model = onboarding_models.FreelancerBusinessApply
        fields = [
            "uid",
            "business_uid",
            "freelancer_uid",
            "status",
        ]
        read_only_fields = [
            "uid",
            "business_uid",
            "freelancer_uid",
        ]
    
    def validate_status(self, value):
        user = self.context["request"].user
        if user == self.instance.freelancer.user:
            if value != onboarding_enums.ApplicationStatusChoices.CANCELED:
                raise serializers.ValidationError(_("You can only cancel your application as a freelancer."))
        if user == self.instance.business.user:
            if value not in [
                onboarding_enums.ApplicationStatusChoices.APPROVED,
                onboarding_enums.ApplicationStatusChoices.REJECTED,
            ]:
                raise serializers.ValidationError(_("You can only approve or reject the application as a business."))
        return value

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if user != instance.freelancer.user and user != instance.business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        celery_app.send_task(
            "send_apply_response_notification",
            args=[instance.uid],
        )
        celery_app.send_task(
            "send_apply_response_email",
            args=[instance.uid],
        )
        return super().update(instance, validated_data)


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    business = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    services = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )
    class Meta:
        model = business_models.Employee
        fields = [
            "uid",
            "business",
            "services",
            "name",
            "avatar",
        ]
        read_only_fields = [
            "uid",
        ]
    
    def validate_services(self, value):
        services = business_models.Service.objects.filter(
            uid__in=value,
        )
        if not services.exists():
            raise serializers.ValidationError(_("Invalid services."))
        return services

    def validate_business(self, value):
        business = business_models.Business.objects.filter(
            uid=value,
        ).first()
        if not business:
            raise serializers.ValidationError(_("Invalid business uid."))
        user = self.context["request"].user
        if not user == business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return business

    def update(self, instance, validated_data):
        services = validated_data.pop("services", [])
        instance = super().update(instance, validated_data)
        if services:
            instance.services.set(services)
        return instance


class WorkingHoursCreateEmployeeSerializer(serializers.ModelSerializer):
    employee = serializers.UUIDField(
        write_only=True,
        required=True,
    )
    class Meta:
        model = business_models.WorkingHours
        fields = [
            "uid",
            "employee",
            "day_of_week",
            "start_time",
            "end_time",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate_employee(self, value):
        employee = business_models.Employee.objects.filter(
            uid=value,
        ).first()
        if not employee:
            raise serializers.ValidationError(_("Invalid employee uid."))
        user = self.context["request"].user
        if not user == employee.business.user:
            raise serializers.ValidationError(_("You are not the owner of this business."))
        return employee
    
    def create(self, validated_data):
        employee = validated_data.pop("employee", None)

        day = validated_data["day_of_week"]
        start = validated_data["start_time"]
        end = validated_data["end_time"]

        instance = business_models.WorkingHours.objects.filter(
            day_of_week=day,
            start_time=start,
            end_time=end,
        ).first()

        if instance is None:
            instance = business_models.WorkingHours.objects.create(
                day_of_week=day,
                start_time=start,
                end_time=end,
            )

        employee.working_hours.add(instance)
        return instance


class FreelancerCreateSerializer(serializers.ModelSerializer):
    services_offered = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
    )
    location = LocationPointDisplaySerializer(required=True)
    uid = serializers.UUIDField(
        read_only=True,
    )

    class Meta:
        model = onboarding_models.FreeLancer
        fields = [
            "services_offered",
            "location",
            "uid",
        ]
        read_only_fields = [
            "uid",
        ]
    
    def validate_location(self, value: dict):
        return GeoUtils.dict_to_point(value)

    def validate_services_offered(self, value):
        services_offered = business_models.ServiceCategory.objects.filter(
            uid__in=value,
        )
        return services_offered

    def validate(self, attrs):
        user = self.context["request"].user
        attrs["user"] = user
        if onboarding_models.FreeLancer.objects.filter(
            user=user,
        ).exists():
            raise serializers.ValidationError(_("You already have a freelancer profile."))
        return super().validate(attrs)
    
    def create(self, validated_data):
        services_offered = validated_data.pop("services_offered", [])
        services_offered_ids = [service.id for service in services_offered]
        instance = super().create(validated_data)
        if services_offered:
            instance.services_offered.set(services_offered_ids)
        return instance
    

class FreelancerUpdateSerializer(FreelancerCreateSerializer):
    class Meta:
        model = onboarding_models.FreeLancer
        fields = [
            "services_offered",
            "location",
            "uid",
        ]
        read_only_fields = [
            "uid",
        ]

    def validate(self, attrs):
        return attrs
    
    def update(self, instance, validated_data):
        services_offered = validated_data.pop("services_offered", [])
        services_offered_ids = [service.id for service in services_offered]
        instance = super().update(instance, validated_data)
        if services_offered:
            instance.services_offered.set(services_offered_ids)
        return instance


class FreelancerDetailSerializer(serializers.ModelSerializer):
    business = business_serializers.BusinessShortListSerializer(
        default=None,
        source="user.first_business"
    )
    services_offered = business_serializers.ServiceCategorySerializer(
        many=True,
        read_only=True,
    )
    location = LocationPointDisplaySerializer(
        read_only=True,
    )
    user_uid = serializers.UUIDField(
        source="user.uid",
        read_only=True,
    )
    employee_uid = serializers.UUIDField(
        source="employee.uid",
        read_only=True,
        default=None,
    )
    costumer_uid = serializers.UUIDField(
        source="user.costumer.uid",
        read_only=True,
    )
    uid = serializers.UUIDField(
        read_only=True,
    )

    class Meta:
        model = onboarding_models.FreeLancer
        fields = [
            "uid",
            "user_uid",
            "employee_uid",
            "costumer_uid",
            "services_offered",
            "location",
            "business",
        ]


class FreelancerApplyListSerializer(serializers.ModelSerializer):
    business_uid = serializers.UUIDField(
        source="business.uid",
        read_only=True,
    )
    business = business_serializers.BusinessShortListSerializer(
        default=None,
    )
    freelancer_uid = serializers.UUIDField(
        source="freelancer.uid",
        read_only=True,
    )
    freelancer = FreelancerDetailSerializer(
        default=None,
    )
    class Meta:
        model = onboarding_models.FreelancerBusinessApply
        fields = [
            "uid",
            "business_uid",
            "business",
            "freelancer_uid",
            "freelancer",
            "status",
            "created_at",
        ]