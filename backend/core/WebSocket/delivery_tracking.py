"""
WebSocket consumer - broadcasts live GPS location of delivery partner to customer.
Customer connects: ws://localhost:8000/ws/delivery/<order_id>/tracking/
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection

from auth.jwt_utils import verify_token

logger = logging.getLogger('core')


class DeliveryTrackingConsumer(AsyncWebsocketConsumer):
    """Live delivery partner location tracking."""

    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f'tracking_{self.order_id}'

        # Authenticate via query string token
        query = self.scope['query_string'].decode()
        token = None
        for part in query.split('&'):
            if part.startswith('token='):
                token = part[6:]
                break

        if not token:
            await self.close(code=4001)
            return

        try:
            payload = verify_token(token)
            self.user_id = payload.get('user_id')
            self.user_role = payload.get('role')
        except Exception:
            await self.close(code=4001)
            return

        # Verify access
        has_access = await self._verify_access()
        if not has_access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send latest known location on connect
        location = await self._get_latest_location()
        if location:
            await self.send(text_data=json.dumps({
                'type': 'current_location',
                'order_id': self.order_id,
                'lat': location['lat'],
                'lng': location['lng'],
                'updated_at': location['updated_at'],
            }))

        logger.info(f'Tracking WebSocket connected: order={self.order_id}')

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Client messages (ping)."""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass

    # ============================================================================
    # Group event handler
    # ============================================================================
    async def location_update(self, event):
        """Called when location_broadcast() is invoked."""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'order_id': event['order_id'],
            'lat': event['lat'],
            'lng': event['lng'],
            'timestamp': event.get('timestamp'),
        }))

    # ============================================================================
    # DB
    # ============================================================================
    @database_sync_to_async
    def _verify_access(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT customer_id, delivery_partner_id
                FROM orders WHERE id = %s
            """, [self.order_id])
            row = cursor.fetchone()
            if not row:
                return False

            customer_id, partner_id = row

            if self.user_role == 'customer' and customer_id == self.user_id:
                return True
            if self.user_role == 'delivery_partner' and partner_id == self.user_id:
                return True
            if self.user_role == 'admin':
                return True
        return False

    @database_sync_to_async
    def _get_latest_location(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT lat, lng, updated_at FROM delivery_locations
                WHERE order_id = %s ORDER BY updated_at DESC LIMIT 1
            """, [self.order_id])
            row = cursor.fetchone()
            if row:
                return {
                    'lat': float(row[0]),
                    'lng': float(row[1]),
                    'updated_at': row[2].isoformat() if row[2] else None,
                }
        return None