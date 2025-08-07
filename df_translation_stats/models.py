from datetime import datetime
from pydantic import BaseModel, computed_field


class Attributes(BaseModel):
    translated_strings: int
    total_strings: int
    last_translation_update: datetime | None = None


class ResourceLanguageStats(BaseModel):
    id: str
    attributes: Attributes

    @computed_field
    @property
    def language_code(self) -> str:
        return self.id.split(":")[-1]

    @computed_field
    @property
    def resource_code(self) -> str:
        return self.id.split(":")[-3]


class TranslationStats(BaseModel):
    data: list[ResourceLanguageStats]
