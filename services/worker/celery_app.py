"""
Celery Worker Configuration for OpenTrace
"""
import os
import sys
from celery import Celery

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from apps.api.app.config import settings

celery_app = Celery(
    "opentrace_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["services.worker.tasks.search_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)

