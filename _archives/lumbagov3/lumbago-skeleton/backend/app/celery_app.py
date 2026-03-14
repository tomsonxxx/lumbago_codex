import os
from celery import Celery
broker = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
celery = Celery('lumbago', broker=broker, backend=backend)
celery.conf.task_routes = {
    'backend.app.ai_service.analyze_track_task': {'queue': 'ai'}
}
