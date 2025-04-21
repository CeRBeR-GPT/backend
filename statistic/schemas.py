import uuid
import logging

from datetime import datetime, date
from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field

from src.transactions.schemas import AvailableProviders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderStatistic(BaseModel):
    provider_name: AvailableProviders
    messages_sent: int = 0
    last_activity: Optional[datetime] = None


class DayStatistic(BaseModel):
    day: date = Field(default_factory=date.today)
    providers: List[ProviderStatistic] = Field(default_factory=list)

    def get_provider(self, provider_name: str) -> ProviderStatistic:
        for provider in self.providers:
            if provider.provider_name == provider_name:
                return provider

        new_provider = ProviderStatistic(provider_name=provider_name)
        self.providers.append(new_provider)
        return new_provider


class StatisticResponse(BaseModel):
    user_id: uuid.UUID
    statistics: List[DayStatistic]


class UserDocument(Document):
    user_id: uuid.UUID = Field(..., unique=True)
    statistics: List[DayStatistic] = []

    class Settings:
        name = "users"

    async def add_message(
            self,
            provider: AvailableProviders,
            count: int = 1,
            target_date: date = None
    ) -> None:
        if target_date is None:
            target_date = date.today()
        logger.info(f"Day from param: {target_date}")

        day_stat = None
        for s in self.statistics:
            if s.day == target_date:
                day_stat = s
                break

        if not day_stat:
            day_stat = DayStatistic(day=target_date)
            self.statistics.append(day_stat)

        logger.info(f"Date from day stat: {day_stat.day}")

        provider = day_stat.get_provider(provider.value)
        provider.messages_sent += count
        provider.last_activity = datetime.now()

        await self.save()

