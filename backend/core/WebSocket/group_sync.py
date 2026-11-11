"""
Group Order WebSocket Consumer - real-time cart sync.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection
from decimal import Decimal

from auth.jwt_utils import verify_token

logger = logging.getLogger('core')


class GroupOrderConsumer(AsyncWebsocketConsumer):
    """Real-time sync for group order participants."""

    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f'group_{self.group_id}'

        # Auth via token in query string
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
        except Exception:
            await self.close(code=4001)
            return

        # Verify group exists and user has access
        access = await self._verify_access()
        if not access:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current state immediately
        state = await self._get_group_state()
        if state:
            await self.send(text_data=json.dumps({
                'type': 'current_state',
                **state,
            }))

        logger.info(f'Group WS connected: group={self.group_id}, user={self.user_id}')

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

    # Group event handler
    async def group_update(self, event):
        """Called when broadcast_group_update is invoked."""
        state = await self._get_group_state()
        if state:
            await self.send(text_data=json.dumps({
                'type': 'state_update',
                **state,
            }))

    # DB access
    @database_sync_to_async
    def _verify_access(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT host_id, status FROM group_orders WHERE id = %s
            """, [self.group_id])
            row = cursor.fetchone()
            if not row:
                return False
            # Allow if host OR has added items
            if row[0] == self.user_id:
                return True
            cursor.execute("""
                SELECT COUNT(*) FROM group_order_items
                WHERE group_order_id = %s AND user_id = %s
            """, [self.group_id, self.user_id])
            if cursor.fetchone()[0] > 0:
                return True
            # Allow anyone with the link (for join flow)
            return row[1] == 'open'

    @database_sync_to_async
    def _get_group_state(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT status, host_id FROM group_orders WHERE id = %s
            """, [self.group_id])
            g = cursor.fetchone()
            if not g:
                return None

            cursor.execute("""
                SELECT id, user_id, user_name, menu_item_id, item_name,
                       item_price, quantity
                FROM group_order_items
                WHERE group_order_id = %s
                ORDER BY added_at
            """, [self.group_id])

            items = []
            members = {}
            total = Decimal('0')

            for r in cursor.fetchall():
                subtotal = Decimal(str(r[5])) * r[6]
                total += subtotal
                items.append({
                    'id': r[0],
                    'user_id': r[1],
                    'user_name': r[2],
                    'menu_item_id': r[3],
                    'name': r[4],
                    'price': float(r[5]),
                    'quantity': r[6],
                    'subtotal': float(subtotal),
                })
                if r[1] not in members:
                    members[r[1]] = {'user_id': r[1], 'name': r[2], 'subtotal': 0}
                members[r[1]]['subtotal'] += float(subtotal)

            return {
                'group_id': self.group_id,
                'status': g[0],
                'items': items,
                'members': list(members.values()),
                'subtotal': float(total),
                'member_count': len(members),
            }