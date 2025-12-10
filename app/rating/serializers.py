from rest_framework import serializers
from rating import models as rating_models
from business import models as business_models
from django.utils.translation import gettext_lazy as _


from user import serializers as user_serializers


class RatingAddSerializer(serializers.ModelSerializer):
    """
    Serializer for adding rating.
    """
    booking = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the booking associated with the rating.",
        required=False,
        allow_null=True,
    )
    business = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the service for which the rating is being added.",
        required=False,
        allow_null=False,
    )
    employee = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the employee for whom the rating is being added.",
        required=False,
        allow_null=True,
    )
    reply_to = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the rating to which this rating is a reply.",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = rating_models.Rating
        fields = [
            'uid',
            'booking',
            'business',
            'employee',
            'rating',
            'comment',
            'reply_to',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'uid',
            'created_at',
            'updated_at',
        ]

    def validate_booking(self, value):
        if not value:
            return None
        booking = business_models.UserBusinesBooking.objects.filter(uid=value).first()
        if not booking:
            raise serializers.ValidationError(_("Booking does not exist."))
        return booking
    
    def validate_employee(self, value):
        if not value:
            return None
        employee = business_models.Employee.objects.filter(uid=value).first()
        if not employee:
            raise serializers.ValidationError(_("Employee does not exist."))
        return employee

    def validate_business(self, value):
        business = business_models.Business.objects.filter(uid=value).first()
        if not business:
            raise serializers.ValidationError(_("Business does not exist."))
        return business

    def validate_reply_to(self, value):
        if not value:
            return None
        rating = rating_models.Rating.objects.filter(uid=value).first()
        if not rating:
            raise serializers.ValidationError(_("Rating does not exist."))
        return rating

    def validate(self, attrs):
        user = self.context['request'].user
        attrs['user'] = user

        employee = attrs.get('employee')
        business = attrs.get('business')
        if employee and business:
            raise serializers.ValidationError(_("You cannot rate both business and employee at the same time."))
        
        # allow user to to do only 1 rating per business or 1 rating per employee
        if employee:
            existing_rating = rating_models.Rating.objects.filter(
                user=user,
                employee=employee
            ).first()
            if existing_rating:
                raise serializers.ValidationError(_("You have already rated this employee."))
        if business:
            existing_rating = rating_models.Rating.objects.filter(
                user=user,
                business=business
            ).first()
            if existing_rating:
                raise serializers.ValidationError(_("You have already rated this business."))
        return super().validate(attrs)
    

class RatingEditSerializer(serializers.ModelSerializer):
    """
    Serializer for editing rating.
    """

    class Meta:
        model = rating_models.Rating
        fields = [
            'uid',
            'rating',
            'comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'uid',
            'created_at',
            'updated_at',
        ]



class RatingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing ratings.
    """
    booking = serializers.UUIDField(
        read_only=True,
        source='booking.uid',
        help_text="The UUID of the booking associated with the rating.",
    )
    business = serializers.UUIDField(
        read_only=True,
        source='business.uid',
        help_text="The UUID of the service for which the rating is being listed.",
    )
    employee = serializers.UUIDField(
        read_only=True,
        source='employee.uid',
        help_text="The UUID of the employee for whom the rating is being listed.",
    )
    user = user_serializers.userInlineDetailsSerializer(
        read_only=True,
        help_text="The user who created the rating.",
    )
    reply_to = serializers.UUIDField(
        read_only=True,
        source='reply_to.uid',
        help_text="The UUID of the rating to which this rating is a reply.",
    )
    replies_count = serializers.SerializerMethodField()

    def get_replies_count(self, obj) -> int:
        return obj.replies.count()

    class Meta:
        model = rating_models.Rating
        fields = [
            'uid',
            'booking',
            'business',
            'employee',
            'user',
            'rating',
            'comment',
            'reply_to',
            'replies_count',
            'created_at',
            'updated_at',
        ]


class UserBusinessSaveSerializer(serializers.ModelSerializer):
    """
    Serializer for saving a business.
    """
    business = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the service to be saved.",
        required=True,
        allow_null=False,
    )

    class Meta:
        model = rating_models.UserBusinessSave
        fields = [
            'business',
            'created_at',
        ]
        read_only_fields = [
            'created_at',
        ]

    def validate_business(self, value):
        business = business_models.Business.objects.filter(uid=value).first()
        if not business:
            raise serializers.ValidationError(_("Business does not exist."))
        return business
    
    def validate(self, attrs):
        user = self.context['request'].user
        attrs['user'] = user
        return super().validate(attrs)


class UserBusinessFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for favoriting a business.
    """
    business = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the service to be favorited.",
        required=True,
        allow_null=False,
    )

    class Meta:
        model = rating_models.UserBusinessFavorite
        fields = [
            'business',
            'created_at',
        ]
        read_only_fields = [
            'created_at',
        ]

    def validate_business(self, value):
        business = business_models.Business.objects.filter(uid=value).first()
        if not business:
            raise serializers.ValidationError(_("Business does not exist."))
        return business
    
    def validate(self, attrs):
        user = self.context['request'].user
        attrs['user'] = user
        return super().validate(attrs)


class UserEmployeeFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for favoriting an employee.
    """
    employee = serializers.UUIDField(
        write_only=True,
        help_text="The UUID of the employee to be favorited.",
        required=True,
        allow_null=False,
    )

    class Meta:
        model = rating_models.UserEmployeeFavorite
        fields = [
            'employee',
            'created_at',
        ]
        read_only_fields = [
            'created_at',
        ]

    def validate_employee(self, value):
        employee = business_models.Employee.objects.filter(uid=value).first()
        if not employee:
            raise serializers.ValidationError(_("Employee does not exist."))
        return employee
    
    def validate(self, attrs):
        user = self.context['request'].user
        attrs['user'] = user
        return super().validate(attrs)
