"""
Email service - send transactional emails.
Called synchronously or via Celery tasks.
"""
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.db import connection

logger = logging.getLogger('core')


def send_email(to_email: str, subject: str, body: str, html_body: str = None) -> bool:
    """
    Send an email (plain text + optional HTML).
    Returns True on success, False on failure.
    """
    if not to_email:
        logger.warning('send_email called with empty to_email')
        return False

    try:
        if html_body:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=[to_email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
        else:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[to_email],
                fail_silently=False,
            )
        logger.info(f'Email sent to {to_email}: {subject}')
        return True
    except Exception as e:
        logger.error(f'Failed to send email to {to_email}: {e}')
        return False


# ============================================================================
# Email templates - rendered as HTML
# ============================================================================
def _wrap_html(title: str, body_html: str) -> str:
    """Wrap content in a basic HTML template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #e23744; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8f8f8; padding: 20px; border-radius: 0 0 8px 8px; }}
        .btn {{ background: #e23744; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        .total {{ font-weight: bold; font-size: 18px; color: #e23744; }}
      </style>
    </head>
    <body>
      <div class="header"><h2>{title}</h2></div>
      <div class="content">{body_html}</div>
    </body>
    </html>
    """


# ============================================================================
# Transactional email helpers
# ============================================================================
def send_order_confirmation_email(order_id: str):
    """Send order confirmation email to customer."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, o.final_amount, o.payment_method, o.placed_at,
                   o.estimated_delivery_time,
                   c.name, c.email,
                   r.name as restaurant_name
            FROM orders o
            JOIN users c ON c.id = o.customer_id
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        row = cursor.fetchone()
        if not row:
            return False

        # Get items
        cursor.execute("""
            SELECT item_name, item_price, quantity, subtotal
            FROM order_items WHERE order_id = %s
        """, [order_id])
        items = cursor.fetchall()

    items_html = ''.join(
        f'<tr><td>{i[0]}</td><td>{i[2]}</td><td>₹{float(i[1]):.2f}</td><td>₹{float(i[3]):.2f}</td></tr>'
        for i in items
    )

    body_html = f"""
        <p>Hi <b>{row[5]}</b>,</p>
        <p>Thank you for your order from <b>{row[7]}</b>!</p>
        <p><b>Order ID:</b> {row[0][:8].upper()}<br>
        <b>Payment:</b> {row[2].upper()}<br>
        <b>Estimated delivery:</b> {row[4]} minutes</p>
        <h3>Items:</h3>
        <table>
          <tr><th>Item</th><th>Qty</th><th>Price</th><th>Subtotal</th></tr>
          {items_html}
        </table>
        <p class="total">Total: ₹{float(row[1]):.2f}</p>
        <p>You can track your order anytime from the app.</p>
    """

    plain_body = f"""Hi {row[5]},

Your order from {row[7]} has been placed.

Order ID: {row[0][:8].upper()}
Amount: ₹{row[1]}
Payment: {row[2].upper()}

Track your order in the app.
"""

    return send_email(
        to_email=row[6],
        subject=f'Order Confirmed - #{row[0][:8].upper()}',
        body=plain_body,
        html_body=_wrap_html('Order Confirmed!', body_html),
    )


def send_order_delivered_email(order_id: str):
    """Email customer when order is delivered."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, c.name, c.email, r.name
            FROM orders o
            JOIN users c ON c.id = o.customer_id
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        row = cursor.fetchone()
        if not row:
            return False

    body_html = f"""
        <p>Hi <b>{row[1]}</b>,</p>
        <p>Your order from <b>{row[3]}</b> has been delivered. Enjoy your meal!</p>
        <p>We'd love to hear about your experience. Please rate your order in the app.</p>
    """
    plain = f"Hi {row[1]},\n\nYour order from {row[3]} has been delivered. Enjoy!"

    return send_email(
        to_email=row[2],
        subject=f'Delivered - Order #{row[0][:8].upper()}',
        body=plain,
        html_body=_wrap_html('Order Delivered!', body_html),
    )


def send_order_cancelled_email(order_id: str):
    """Email customer when order is cancelled."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT o.id, c.name, c.email, r.name, o.cancel_reason, o.cancelled_by
            FROM orders o
            JOIN users c ON c.id = o.customer_id
            JOIN restaurants r ON r.id = o.restaurant_id
            WHERE o.id = %s
        """, [order_id])
        row = cursor.fetchone()
        if not row:
            return False

    body_html = f"""
        <p>Hi <b>{row[1]}</b>,</p>
        <p>Your order from <b>{row[3]}</b> has been cancelled.</p>
        <p><b>Reason:</b> {row[4] or 'Not specified'}<br>
        <b>Cancelled by:</b> {row[5]}</p>
        <p>If you paid online, the amount will be refunded within 5-7 business days.</p>
    """
    plain = f"Order #{row[0][:8].upper()} has been cancelled. Reason: {row[4] or 'N/A'}"

    return send_email(
        to_email=row[2],
        subject=f'Order Cancelled - #{row[0][:8].upper()}',
        body=plain,
        html_body=_wrap_html('Order Cancelled', body_html),
    )


def send_welcome_email(user_id: str):
    """Welcome email on registration."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name, email, role FROM users WHERE id = %s", [user_id])
        row = cursor.fetchone()
        if not row:
            return False

    role_msg = {
        'customer': 'Browse restaurants, order food, and enjoy!',
        'restaurant_owner': 'Set up your restaurant and start accepting orders.',
        'delivery_partner': 'Start earning by delivering orders in your area.',
        'admin': 'You have full admin access to the platform.',
    }.get(row[2], 'Welcome aboard!')

    body_html = f"""
        <p>Hi <b>{row[0]}</b>,</p>
        <p>Welcome to Food Delivery! Your account has been created successfully.</p>
        <p><b>Role:</b> {row[2].replace('_', ' ').title()}</p>
        <p>{role_msg}</p>
    """
    plain = f"Hi {row[0]}, welcome to Food Delivery!"

    return send_email(
        to_email=row[1],
        subject='Welcome to Food Delivery!',
        body=plain,
        html_body=_wrap_html('Welcome!', body_html),
    )