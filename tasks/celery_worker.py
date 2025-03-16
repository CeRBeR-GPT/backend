import asyncio

from celery import Celery
from celery.schedules import crontab

from src.users.repositories import UserRepository
from utils.ai_settings import generate_ai_response
from utils.email_sender import send_verification_code

celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    include=['tasks']
)


@celery_app.task
def task_send_to_email(email, code):
    send_verification_code(email, code)


@celery_app.task
def task_generate_ai_response(message, history) -> str:
    return generate_ai_response(message, history)


@celery_app.task
def task_daily_reset_available_messages():
    return asyncio.run(UserRepository().reset_available_messages())


celery_app.conf.beat_schedule = {
    'task-daily-messages': {
        'task': 'tasks.celery_worker.task_daily_reset_available_messages',
        'schedule': crontab(hour="10", minute="25"),
    },
}

celery_app.conf.timezone = 'UTC'
