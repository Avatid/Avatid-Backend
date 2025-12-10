
from django_filters import rest_framework as filters

from notifications import models as notifications_models
from notifications.enums import NotificationType, OrderByChoices



class NotificationFilter(filters.FilterSet):
    ORDER_BY_MAP = {
        OrderByChoices.NEWEST: '-sent_at',
        OrderByChoices.OLDEST: 'sent_at',
    }

    order_by = filters.CharFilter(method='filter_order_by')
    notification_type = filters.CharFilter(
        field_name='notification_type',
        lookup_expr='iexact',
    )
    

    class Meta:
        model = notifications_models.NotificationObject
        fields = (
            'order_by',
            'notification_type',
        )

    def filter_order_by(self, queryset, name, value):
        """Ensure DISTINCT ON(field) compatibility by always ordering first by that field.

        PostgreSQL requires that the ORDER BY list starts with the DISTINCT ON
        expressions. Since the view applies distinct('normalized_id'), any
        subsequent re-ordering must keep 'normalized_id' as the leading order
        expression to avoid: "SELECT DISTINCT ON expressions must match initial ORDER BY expressions".

        We therefore prepend 'normalized_id' to the dynamic ordering field chosen
        by the client. If the client passes an unknown value we just keep the
        existing ordering (which already starts with normalized_id from the view).
        """
        order_field = self.ORDER_BY_MAP.get(value)
        if order_field:
            # Prepend normalized_id so DISTINCT ON(normalized_id) remains valid
            return queryset.order_by('normalized_id', order_field)
        return queryset
    
    

