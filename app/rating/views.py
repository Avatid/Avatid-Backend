from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django_filters import rest_framework as drf_filters
from django.utils.translation import gettext_lazy as _

from business import models as business_models

from rating import serializers as rating_serializers
from rating import models as rating_models
from rating import filters as rating_filters
from rating import enums as rating_enums



class MyRatingView(generics.ListAPIView):
    """
    API view to list the user's feedback.
    """
    serializer_class = rating_serializers.RatingListSerializer
    queryset = rating_models.Rating.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = rating_filters.RatingFilter
    
    def get_queryset(self):
        return rating_models.Rating.objects.filter(user=self.request.user).order_by('-created_at')


class AddRatingView(generics.CreateAPIView):
    """
    API view to add feedback for a business.
    """
    serializer_class = rating_serializers.RatingAddSerializer
    permission_classes = [IsAuthenticated]


class RatingListView(generics.ListAPIView):
    """
    API view to list feedback for a business.
    """
    serializer_class = rating_serializers.RatingListSerializer
    queryset = rating_models.Rating.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = rating_filters.RatingFilter

    def get_queryset(self):
        business_uid = self.kwargs['business_uid']
        return rating_models.Rating.objects.filter(
            business__uid=business_uid,
            reply_to__isnull=True
        ).order_by('-created_at')
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='sort_by',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Sort ratings by this field.',
                enum=[
                    choice.value for choice in rating_enums.SortByChoices
                ]
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Override the get method to apply sorting based on query parameters.
        """
        return super().get(request, *args, **kwargs)
    

class RatingBookingListView(RatingListView):
    def get_queryset(self):
        booking_uid = self.kwargs.get('booking_uid')
        return rating_models.Rating.objects.filter(
            booking__uid=booking_uid,
            reply_to__isnull=True
        ).order_by('-created_at')
    

class RatingEmployeeListView(generics.ListAPIView):
    """
    API view to list feedback for an employee.
    """
    serializer_class = rating_serializers.RatingListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (drf_filters.DjangoFilterBackend,)
    filterset_class = rating_filters.RatingFilter

    def get_queryset(self):
        employee_uid = self.kwargs['employee_uid']
        return rating_models.Rating.objects.filter(
            employee__uid=employee_uid,
            reply_to__isnull=True
        ).order_by('-created_at')

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='sort_by',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Sort ratings by this field.',
                enum=[
                    choice.value for choice in rating_enums.SortByChoices
                ]
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Override the get method to apply sorting based on query parameters.
        """
        return super().get(request, *args, **kwargs)


class RatingRepliesView(generics.ListAPIView):
    """
    API view to list replies for a feedback.
    """
    serializer_class = rating_serializers.RatingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        rating_uid = self.kwargs['rating_uid']
        return rating_models.Rating.objects.filter(
            reply_to__uid=rating_uid
        ).order_by('-created_at')
    

class DeleteRatingView(generics.DestroyAPIView):
    """
    API view to delete a feedback.
    """
    permission_classes = [IsAuthenticated]
    queryset = rating_models.Rating.objects.all()
    lookup_field = 'uid'


class EditRatingView(generics.UpdateAPIView):
    """
    API view to edit a feedback.
    """
    serializer_class = rating_serializers.RatingEditSerializer
    permission_classes = [IsAuthenticated]
    queryset = rating_models.Rating.objects.all()
    lookup_field = 'uid'
    allowed_methods = ['PATCH']



class SaveBusinessView(generics.CreateAPIView):
    """
    API view to save a business.
    """
    serializer_class = rating_serializers.UserBusinessSaveSerializer
    permission_classes = [IsAuthenticated]


class UnsaveBusinessView(generics.DestroyAPIView):
    """
    API view to unsave a business.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        business_uid = self.kwargs['business_uid']
        return rating_models.UserBusinessSave.objects.filter(
            user=self.request.user,
            business__uid=business_uid
        )
    

class FavoriteBusinessView(generics.CreateAPIView):
    """
    API view to favorite a business.
    """
    serializer_class = rating_serializers.UserBusinessFavoriteSerializer
    permission_classes = [IsAuthenticated]


class UnfavoriteBusinessView(generics.DestroyAPIView):
    """
    API view to unfavorite a business.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        business_uid = self.kwargs['business_uid']
        return rating_models.UserBusinessFavorite.objects.filter(
            user=self.request.user,
            business__uid=business_uid
        )
    

class FavoriteEmployeeView(generics.CreateAPIView):
    """
    API view to favorite an employee.
    """
    serializer_class = rating_serializers.UserEmployeeFavoriteSerializer
    permission_classes = [IsAuthenticated]


class UnfavoriteEmployeeView(generics.DestroyAPIView):
    """
    API view to unfavorite an employee.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        employee_uid = self.kwargs['employee_uid']
        return rating_models.UserEmployeeFavorite.objects.filter(
            user=self.request.user,
            employee__uid=employee_uid
        )


