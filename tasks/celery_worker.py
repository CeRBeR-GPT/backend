import asyncio

from celery import Celery
from celery.schedules import crontab

from src.users.repositories import UserRepository
from utils.email_sender import send_letter
from config_data.config import Config, load_config

settings: Config = load_config()
redis_data = settings.redis

celery_app = Celery(
    'tasks',
    broker=redis_data.REDIS_URL,
    backend=redis_data.REDIS_URL,
    include=['tasks']
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        'visibility_timeout': 3600,
        'max_retries': 5,
    },
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    acks_late=True
)
def task_send_to_email(self, subject, body, address):  # noqa: F841
    send_letter(subject=subject, body=body, address=address)


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=300,
    acks_late=True
)
def task_daily_users_update(*args):  # noqa: F841
    asyncio.run(daily_users_update())


async def daily_users_update():
    repo = UserRepository()
    await repo.reset_available_messages()
    await repo.reset_users_plan_to_default()
    await repo.delete_old_default_users_messages()

    return "successful update!"


celery_app.conf.beat_schedule = {
    'task-daily-messages': {
        'task': 'tasks.celery_worker.task_daily_users_update',
        'schedule': crontab(hour="21", minute="00"),
    },
}

celery_app.conf.timezone = 'UTC'
