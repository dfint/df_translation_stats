from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

if TYPE_CHECKING:
    from collections.abc import Iterable

LanguageName = NewType("LanguageName", str)
ResourceName = NewType("ResourceName", str)


@dataclass
class Dataset:
    data: dict[str, dict[str, int]]
    languages: list[str]
    total_lines: int

    @property
    def resources(self) -> list[str]:
        return list(self.data.keys())

    def with_languages(self, languages: list[str]) -> Dataset:
        return Dataset(data=self.data, languages=languages, total_lines=self.total_lines)

    def get_count_by_languages(self) -> dict[str, int]:
        return {language: sum(item[language] for item in self.data.values()) for language in self.languages}

    def sort_languages(self) -> None:
        count_by_language = self.get_count_by_languages()
        self.languages = sorted(
            self.languages,
            key=lambda language: (-count_by_language[language], language),
        )

    @staticmethod
    def filter_languages_by_minmal_translation_count(
        languages: Iterable[str],
        count_by_language: dict[str, int],
        minimal_count: float,
    ) -> list[str]:
        return [language for language in languages if count_by_language[language] > minimal_count]

    def with_minimal_translation_percent(self, minimal_percent: float) -> Dataset:
        languages = self.filter_languages_by_minmal_translation_count(
            languages=self.languages,
            count_by_language=self.get_count_by_languages(),
            minimal_count=minimal_percent / 100 * self.total_lines,
        )
        return self.with_languages(languages)
