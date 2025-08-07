from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

from pydantic import BaseModel, computed_field

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime


class Attributes(BaseModel):
    translated_strings: int
    reviewed_strings: int
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


LanguageName = NewType("LanguageName", str)
ResourceName = NewType("ResourceName", str)


@dataclass
class Dataset:
    data: dict[ResourceName, dict[LanguageName, float]]
    languages: list[LanguageName]
    total_lines: int

    @property
    def resources(self) -> list[ResourceName]:
        return list(self.data.keys())

    def with_languages(self, languages: list[LanguageName]) -> Dataset:
        return Dataset(data=self.data, languages=languages, total_lines=self.total_lines)

    def get_count_by_languages(self) -> dict[LanguageName, int]:
        return {language: sum(item[language] for item in self.data.values()) for language in self.languages}

    def sort_languages(self) -> None:
        count_by_language = self.get_count_by_languages()
        self.languages = sorted(
            self.languages,
            key=lambda language: (-count_by_language[language], language),
        )

    @staticmethod
    def filter_languages_by_minmal_translation_count(
        languages: Iterable[LanguageName],
        count_by_language: dict[LanguageName, int],
        minimal_count: int,
    ) -> list[LanguageName]:
        return [language for language in languages if count_by_language[language] > minimal_count]

    def with_minimal_translation_percent(self, minimal_percent: float) -> Dataset:
        languages = self.filter_languages_by_minmal_translation_count(
            languages=self.languages,
            count_by_language=self.get_count_by_languages(),
            minimal_count=minimal_percent / 100 * self.total_lines,
        )
        return self.with_languages(languages)
