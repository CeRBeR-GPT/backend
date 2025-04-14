import uuid

from datetime import datetime, date
from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field

from src.transactions.schemas import AvailableProviders


class ProviderStatistic(BaseModel):
    provider_name: AvailableProviders
    messages_sent: int = 0
    last_activity: Optional[datetime] = None


class DayStatistic(BaseModel):
    day: date = Field(default_factory=date.today)
    providers: List[ProviderStatistic] = []

    def get_provider(self, provider_name: str) -> ProviderStatistic:
        for provider in self.providers:
            if provider.provider_name == provider_name:
                return provider

        new_provider = ProviderStatistic(provider_name=provider_name)
        self.providers.append(new_provider)
        return new_provider


class UserDocument(Document):
    user_id: uuid.UUID = Field(..., unique=True)
    statistics: List[DayStatistic] = []

    class Settings:
        name = "users"

    async def add_message(
            self,
            provider_name: str,
            count: int = 1,
            target_date: date = date.today()
    ) -> None:
        day_stat = next(
            (s for s in self.statistics if s.day == target_date),
            None
        )

        if not day_stat:
            day_stat = DayStatistic(day=target_date)
            self.statistics.append(day_stat)

        provider = day_stat.get_provider(provider_name)
        provider.messages_sent += count
        provider.last_activity = datetime.now()

        await self.save()
