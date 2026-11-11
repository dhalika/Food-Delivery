"""
WebSocket broadcast helpers - call these from any view to push updates to clients.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def broadcast_order_status(order_id: str, status: str, note: str = ''):
    """
    Broadcast order status change to all clients watching this order.
    Call from any view after updating order status.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f'order_{order_id}',
        {
            'type': 'status_update',  # Maps to status_update() method in consumer
            'order_id': str(order_id),
            'status': status,
            'note': note,
            'timestamp': timezone.now().isoformat(),
        }
    )


def broadcast_location(order_id: str, lat: float, lng: float):
    """
    Broadcast delivery partner's location to all clients tracking this order.
    Call from delivery/update_location after inserting new location.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f'tracking_{order_id}',
        {
            'type': 'location_update',  # Maps to location_update() method in consumer
            'order_id': str(order_id),
            'lat': float(lat),
            'lng': float(lng),
            'timestamp': timezone.now().isoformat(),
        }
    )