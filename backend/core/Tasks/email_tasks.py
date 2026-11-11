"""
Celery tasks for scheduled email reports.
"""
from celery import shared_task
import logging

logger = logging.getLogger('core')


@shared_task
def send_daily_sales_report_to_owners():
    """
    Scheduled: Send daily sales email to all restaurant owners at end of day.
    Run daily at 11 PM via celery-beat.
    """
    from django.db import connection
    from core.Notification.email_service import send_email, _wrap_html

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.name, u.email, r.id, r.name,
                   COUNT(o.id) as order_count,
                   COALESCE(SUM(o.final_amount), 0) as revenue
            FROM users u
            JOIN restaurants r ON r.owner_id = u.id
            LEFT JOIN orders o ON o.restaurant_id = r.id
                AND DATE(o.placed_at) = CURDATE()
                AND o.status = 'delivered'
            WHERE u.role = 'restaurant_owner' AND u.is_active = TRUE
            GROUP BY u.id, u.name, u.email, r.id, r.name
        """)
        rows = cursor.fetchall()

    # Group by owner
    owner_data = {}
    for r in rows:
        oid = r[0]
        if oid not in owner_data:
            owner_data[oid] = {'name': r[1], 'email': r[2], 'restaurants': []}
        owner_data[oid]['restaurants'].append({
            'name': r[4], 'orders': r[5], 'revenue': float(r[6]),
        })

    sent = 0
    for oid, data in owner_data.items():
        rest_html = ''.join(
            f'<tr><td>{r["name"]}</td><td>{r["orders"]}</td><td>₹{r["revenue"]:.2f}</td></tr>'
            for r in data['restaurants']
        )
        total_orders = sum(r['orders'] for r in data['restaurants'])
        total_revenue = sum(r['revenue'] for r in data['restaurants'])

        body_html = f"""
            <p>Hi <b>{data['name']}</b>,</p>
            <p>Here's your daily sales summary:</p>
            <table>
                <tr><th>Restaurant</th><th>Orders</th><th>Revenue</th></tr>
                {rest_html}
            </table>
            <p><b>Total Orders:</b> {total_orders}<br>
            <b>Total Revenue:</b> ₹{total_revenue:.2f}</p>
        """

        if send_email(
            to_email=data['email'],
            subject=f'Daily Sales Report - ₹{total_revenue:.2f}',
            body=f"Today's revenue: ₹{total_revenue:.2f} from {total_orders} orders",
            html_body=_wrap_html('Daily Sales Report', body_html),
        ):
            sent += 1

    logger.info(f'Daily sales reports sent: {sent}')
    return sent


@shared_task
def send_weekly_delivery_summary_to_partners():
    """
    Scheduled: Send weekly summary to delivery partners every Monday.
    """
    from django.db import connection
    from core.Notification.email_service import send_email, _wrap_html

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.name, u.email,
                   COUNT(o.id) as delivery_count,
                   COALESCE(SUM(o.final_amount), 0) as revenue_handled
            FROM users u
            LEFT JOIN orders o ON o.delivery_partner_id = u.id
                AND o.status = 'delivered'
                AND o.delivered_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            WHERE u.role = 'delivery_partner' AND u.is_active = TRUE
            GROUP BY u.id, u.name, u.email
        """)
        rows = cursor.fetchall()

    sent = 0
    for r in rows:
        body_html = f"""
            <p>Hi <b>{r[1]}</b>,</p>
            <p>Your weekly delivery summary:</p>
            <p><b>Total Deliveries:</b> {r[3]}<br>
            <b>Total Revenue Handled:</b> ₹{float(r[4]):.2f}</p>
            <p>Keep up the great work!</p>
        """
        if send_email(
            to_email=r[2],
            subject=f'Weekly Summary: {r[3]} deliveries',
            body=f"You completed {r[3]} deliveries this week.",
            html_body=_wrap_html('Weekly Summary', body_html),
        ):
            sent += 1

    logger.info(f'Weekly delivery summaries sent: {sent}')
    return sent