from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, NewType

import httpx
from scour.scour import scourString as scour_string  # noqa: N813

if TYPE_CHECKING:
    from collections.abc import Iterable

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


def minify_svg(data: bytes) -> bytes:
    return scour_string(data.decode("utf-8"), options=SimpleNamespace(strip_ids=True, shorten_ids=True)).encode("utf-8")


def prepare_chart_data(dataset: Dataset) -> dict[str, Any]:
    datasets = [
        dict(
            label=resource,
            data=[lines[label] for label in dataset.languages],
        )
        for resource, lines in dataset.data.items()
    ]

    return dict(
        type="horizontalBar",
        data=dict(labels=dataset.languages, datasets=datasets),
        options=dict(
            scales=dict(
                yAxes=[dict(stacked=True)],
                xAxes=[
                    dict(
                        stacked=True,
                        ticks=dict(
                            beginAtZero=True,
                            max=dataset.total_lines,
                            stepSize=10000,
                        ),
                    ),
                ],
            ),
        ),
    )


def get_chart(
    dataset: Dataset,
    file_format: str = "png",
    width: int = 800,
    height: int = 800,
) -> bytes:
    chart_data = prepare_chart_data(dataset)

    url = "https://quickchart.io/chart"
    payload = dict(
        width=width,
        height=height,
        backgroundColor="rgb(255, 255, 255)",
        format=file_format,
        chart=chart_data,
    )

    headers = {"Content-type": "application/json"}
    response = httpx.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    chart = response.content

    if file_format == "svg":
        chart = minify_svg(chart)

    return chart
