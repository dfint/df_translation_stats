from datetime import datetime
from pydantic import BaseModel, computed_field


class Attributes(BaseModel):
    translated_strings: int
    total_strings: int
    last_translation_update: datetime | None = None


class ResoruceInfo(BaseModel):
    organization: str
    project: str
    resource: str
    language_code: str


class ResourceLanguageStats(BaseModel):
    id: str
    attributes: Attributes

    @computed_field
    @property
    def resource_info(self) -> ResoruceInfo:
        _, organization, _, project, _, resource, _, language_code = self.id.split(":")
        return ResoruceInfo(
            organization=organization,
            project=project,
            resource=resource,
            language_code=language_code,
        )


class TranslationStats(BaseModel):
    data: list[ResourceLanguageStats]
