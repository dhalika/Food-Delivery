"""
WebSocket URL routing.
"""
from django.urls import re_path

from core.WebSocket.order_status import OrderStatusConsumer
from core.WebSocket.delivery_tracking import DeliveryTrackingConsumer
from core.WebSocket.group_sync import GroupOrderConsumer


websocket_urlpatterns = [
    re_path(r'ws/orders/(?P<order_id>[0-9a-f\-]+)/status/$', OrderStatusConsumer.as_asgi()),
    re_path(r'ws/delivery/(?P<order_id>[0-9a-f\-]+)/tracking/$', DeliveryTrackingConsumer.as_asgi()),
    re_path(r'ws/group/(?P<group_id>[0-9a-f\-]+)/$', GroupOrderConsumer.as_asgi()),
]