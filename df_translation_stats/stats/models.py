from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Attributes(BaseModel):
    translated_strings: int
    reviewed_strings: int | None = None
    total_strings: int
    last_translation_update: datetime | None = None


class ResoruceInfo(BaseModel):
    organization: str
    project: str
    resource: str
    language_code: str


class ResourceLanguageStats(BaseModel):
    attributes: Attributes
    resource_info: ResoruceInfo

    @model_validator(mode="before")
    @classmethod
    def compute_resource_info(cls, data: Any) -> Any:
        assert isinstance(data, dict)
        resource_info_id = data.pop("id")
        _, organization, _, project, _, resource, _, language_code = resource_info_id.split(":")
        data["resource_info"] = dict(
            organization=organization,
            project=project,
            resource=resource,
            language_code=language_code,
        )
        return data


class TranslationStats(BaseModel):
    data: list[ResourceLanguageStats] = Field(default_factory=list)
