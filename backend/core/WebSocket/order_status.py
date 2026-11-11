"""
WebSocket consumer - broadcasts order status changes to customer in real-time.
Customer connects: ws://localhost:8000/ws/orders/<order_id>/status/
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection

from auth.jwt_utils import verify_token

logger = logging.getLogger('core')


class OrderStatusConsumer(AsyncWebsocketConsumer):
    """Live order status updates for customers."""

    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f'order_{self.order_id}'

        # Authenticate via token in query string: ?token=xxx
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

        # Verify user has access to this order
        has_access = await self._verify_order_access()
        if not has_access:
            await self.close(code=4003)
            return

        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current status immediately
        current_status = await self._get_current_status()
        await self.send(text_data=json.dumps({
            'type': 'current_status',
            'order_id': self.order_id,
            'status': current_status,
        }))

        logger.info(f'WebSocket connected: order={self.order_id}, user={self.user_id}')

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Client-sent messages (like ping)."""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass

    # ============================================================================
    # Group event handler - called when someone broadcasts to this group
    # ============================================================================
    async def status_update(self, event):
        """Called when order_status_broadcast() is invoked."""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'note': event.get('note', ''),
            'timestamp': event.get('timestamp'),
        }))

    # ============================================================================
    # DB access
    # ============================================================================
    @database_sync_to_async
    def _verify_order_access(self):
        """Verify user has access to this order."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT customer_id, delivery_partner_id, restaurant_id
                FROM orders WHERE id = %s
            """, [self.order_id])
            row = cursor.fetchone()
            if not row:
                return False

            customer_id, partner_id, restaurant_id = row

            # Customer owns the order
            if self.user_role == 'customer' and customer_id == self.user_id:
                return True
            # Delivery partner assigned to it
            if self.user_role == 'delivery_partner' and partner_id == self.user_id:
                return True
            # Restaurant owner
            if self.user_role == 'restaurant_owner':
                cursor.execute("""
                    SELECT owner_id FROM restaurants WHERE id = %s
                """, [restaurant_id])
                r = cursor.fetchone()
                if r and r[0] == self.user_id:
                    return True
            # Admin
            if self.user_role == 'admin':
                return True

        return False

    @database_sync_to_async
    def _get_current_status(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT status FROM orders WHERE id = %s", [self.order_id])
            row = cursor.fetchone()
        return row[0] if row else None