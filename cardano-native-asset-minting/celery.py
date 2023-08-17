import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cardano-native-asset-minting.settings")
app = Celery("cardano-native-asset-minting")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

app.conf.beat_schedule = {
    # Execute the mint every 1 minute; can be configured below
    'mint-1min': {
        'task': 'periodic_mint_and_cleanup',
        'schedule': crontab(minute='*/1'),
    }
}  

