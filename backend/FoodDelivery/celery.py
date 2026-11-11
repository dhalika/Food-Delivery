"""
Celery configuration with scheduled tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FoodDelivery.settings')

app = Celery('FoodDelivery')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Explicitly include task modules
app.autodiscover_tasks([
    'core.Tasks.order_tasks',
    'core.Tasks.email_tasks',
    'core.Tasks.cleanup_tasks',
])

# Beat schedule
app.conf.beat_schedule = {
    'auto-cancel-unaccepted-orders': {
        'task': 'core.Tasks.order_tasks.auto_cancel_unaccepted_orders',
        'schedule': crontab(minute='*/2'),
    },
    'daily-sales-report': {
        'task': 'core.Tasks.email_tasks.send_daily_sales_report_to_owners',
        'schedule': crontab(hour=23, minute=0),
    },
    'weekly-delivery-summary': {
        'task': 'core.Tasks.email_tasks.send_weekly_delivery_summary_to_partners',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
    'cleanup-old-notifications': {
        'task': 'core.Tasks.cleanup_tasks.cleanup_old_read_notifications',
        'schedule': crontab(hour=3, minute=0),
    },
    'cleanup-delivery-locations': {
        'task': 'core.Tasks.cleanup_tasks.cleanup_old_delivery_locations',
        'schedule': crontab(hour='*/6'),
    },
    'cleanup-abandoned-carts': {
        'task': 'core.Tasks.cleanup_tasks.cleanup_abandoned_carts',
        'schedule': crontab(hour=4, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')