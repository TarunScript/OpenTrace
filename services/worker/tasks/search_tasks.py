"""
Celery Search Tasks
"""
import asyncio
from services.worker.celery_app import celery_app
from apps.api.app.services.investigation_service import InvestigationService


@celery_app.task(name="execute_investigation", bind=True, max_retries=2, default_retry_delay=5)
def execute_investigation(self, investigation_id: str, target_username: str, categories=None):
    """
    Executes an investigation job asynchronously via Celery worker with exponential backoff retry.
    """
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            InvestigationService.run_investigation_job(
                investigation_id=investigation_id,
                target_username=target_username,
                categories=categories,
            )
        )
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5)
        raise exc

