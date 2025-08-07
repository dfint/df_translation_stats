from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, NewType

from dotenv import load_dotenv
from langcodes import Language
from loguru import logger

from df_translation_stats.quickchart import get_chart
from df_translation_stats.transifex import get_translation_stats

if TYPE_CHECKING:
    from collections.abc import Iterable

    from df_translation_stats.models import TranslationStats

load_dotenv()

DEFAULT_WIDTH = 600
DEFAULT_LINE_HEIGHT = 14

LanguageName = NewType("LanguageName", str)
ResourceName = NewType("ResourceName", str)


def filter_languages_by_minmal_translation_count(
    languages: Iterable[LanguageName],
    count_by_language: dict[LanguageName, int],
    minimal_count: int,
) -> list[LanguageName]:
    return [language for language in languages if count_by_language[language] > minimal_count]


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

    def with_minimal_translation_percent(self, minimal_percent: float) -> Dataset:
        languages = filter_languages_by_minmal_translation_count(
            languages=self.languages,
            count_by_language=self.get_count_by_languages(),
            minimal_count=minimal_percent / 100 * self.total_lines,
        )
        return self.with_languages(languages)


def prepare_dataset(raw_data: TranslationStats) -> Dataset:
    languages: set[LanguageName] = set()
    total_lines_by_resource: dict[str, int] = {}
    resource_language_stats = defaultdict(lambda: defaultdict(int))

    for row in raw_data.data:
        language = Language.get(row.resource_info.language_code).display_name()
        languages.add(language)
        total_lines_by_resource[row.resource_info.resource] = max(
            total_lines_by_resource.get(row.resource_info.resource, 0),
            row.attributes.total_strings,
        )
        resource_language_stats[row.resource_info.resource][language] = row.attributes.translated_strings

    return Dataset(
        data=resource_language_stats,
        languages=languages,
        total_lines=sum(total_lines_by_resource.values()),
    )


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


def generate_diagram(
    dataset: Dataset,
    width: int,
    height: int,
    output_file: Path,
) -> None:
    chart_data = prepare_chart_data(dataset)
    file_format = output_file.suffix[1:]
    chart = get_chart(chart_data, file_format=file_format, width=width, height=height)
    output_file.write_bytes(chart)
    logger.info(f"{output_file.name} chart file is saved")


def generate_one_diagram(
    output: Path,
    minimal_percent: int = 0,
    width: int = DEFAULT_WIDTH,
    height: int | None = None,
) -> None:
    logger.info(f"output: {output.resolve()}")
    output.parent.mkdir(exist_ok=True, parents=True)

    tx_token = os.getenv("TX_TOKEN")
    raw_data = get_translation_stats(tx_token)
    dataset: Dataset = prepare_dataset(raw_data)
    count_by_language = dataset.get_count_by_languages()

    logger.info(f"{dataset.resources=}")
    logger.info(f"{dataset.languages=}")
    logger.info(f"{dataset.total_lines=}")

    if minimal_percent:
        dataset = dataset.with_minimal_translation_percent(minimal_percent)

    dataset.sort_languages()

    for language in dataset.languages:
        logger.info(f"{language}: {count_by_language[language] / dataset.total_lines * 100:.1f}%")

    height = height or (len(dataset.languages) + 6) * DEFAULT_LINE_HEIGHT
    generate_diagram(dataset, width, height, output)


def main() -> None:
    generate_one_diagram(Path("diagrams") / "dwarf-fortress-steam.svg")


if __name__ == "__main__":
    main()
