from typing import Any, Protocol

from df_translation_stats.stats.models import TranslationStats


class StatsService(Protocol):
    async def get_translation_stats(self) -> TranslationStats:
        raise NotImplemented
    
    async def get_resource_strings_tagged_notranslate(self, resource: str) -> list[dict[str, Any]]:
        raise NotImplemented
