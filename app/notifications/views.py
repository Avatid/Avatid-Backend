from django.shortcuts import render

from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from celery import current_app as celery_app
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from notifications import models as notification_models
from notifications import serializers as notification_serializers

from notifications import notifications_filters
from django_filters import rest_framework as filters
from notifications.enums import NotificationType, OrderByChoices
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from user.permissions import IsOwner


class PushTokenCreateView(generics.CreateAPIView):
    serializer_class = notification_serializers.PushTokenSerializer
    permission_classes = [IsAuthenticated]

class MyNotificationsListView(generics.ListAPIView):
    serializer_class = notification_serializers.NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend, ]
    filterset_class = notifications_filters.NotificationFilter

    def get_queryset(self):
        return (
            notification_models.NotificationObject.get_annotated_objects()
            .filter(user=self.request.user)
            .order_by('normalized_id', '-sent_at')
            .distinct('normalized_id')
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='order_by',
                description=_('Order by'),
                required=False,
                type=OpenApiTypes.STR,
                enum=OrderByChoices.values,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='notification_type',
                description=_('Notification type'),
                required=False,
                type=OpenApiTypes.STR,
                enum=NotificationType.values,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ClearAllNotificationsView(GenericViewSet):
    """
    Clear all notifications of the current user
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def delete(self, request, *args, **kwargs):
        notification_models.NotificationObject.objects.filter(
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class ClearNotificationView(generics.DestroyAPIView):
    """
    Clear notification by uid and delete it
    """
    serializer_class = notification_serializers.NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = notification_models.NotificationObject.objects.all()
    lookup_field = 'uid'
    allowed_methods = ['DELETE',]



class MarkAsReadView(generics.UpdateAPIView):
    serializer_class = notification_serializers.NotificationMarkReadSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    lookup_field = 'uid'
    allowed_methods = ['PATCH',]

    def get_queryset(self):
        return notification_models.NotificationObject.get_annotated_objects().filter(
            user=self.request.user
        ).order_by('-sent_at')  

