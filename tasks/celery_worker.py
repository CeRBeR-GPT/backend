import asyncio

from celery import Celery
from celery.schedules import crontab

from src.users.repositories import UserRepository
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
def task_daily_users_update():
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
