from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NewType

from loguru import logger
import httpx
from dotenv import load_dotenv
from langcodes import Language
from scour.scour import scourString as scour_string  # noqa: N813

from .models import TranslationStats

load_dotenv()

DEFAULT_WIDTH = 600
DEFAULT_LINE_HEIGHT = 14

LanguageName = NewType("LanguageName", str)
ResourceName = NewType("ResourceName", str)


def get_translation_stats(project_id: str) -> TranslationStats:
    tx_token = os.getenv("TX_TOKEN")
    url = "https://rest.api.transifex.com/resource_language_stats"
    headers = {"Authorization": f"Bearer {tx_token}"}
    response = httpx.get(url, params={"filter[project]": project_id}, headers=headers)
    return TranslationStats.model_validate(response.json())


def filter_languages_by_minmal_translation_count(
    languages: Iterable[LanguageName],
    count_by_language: dict[LanguageName, int],
    minimal_count: int,
) -> list[LanguageName]:
    return [
        language
        for language in languages
        if count_by_language[language] > minimal_count
    ]


@dataclass
class Dataset:
    data: dict[ResourceName, dict[LanguageName, float]]
    languages: list[LanguageName]
    total_lines: int

    @property
    def resources(self) -> list[ResourceName]:
        return list(self.data.keys())

    def with_languages(self, languages: list[LanguageName]) -> "Dataset":
        return Dataset(
            data=self.data, languages=languages, total_lines=self.total_lines
        )

    def get_count_by_languages(self) -> dict[LanguageName, int]:
        return {
            language: sum(item[language] for item in self.data.values())
            for language in self.languages
        }

    def sort_languages(self) -> None:
        count_by_language = self.get_count_by_languages()
        self.languages = sorted(
            self.languages,
            key=lambda language: (-count_by_language[language], language),
        )

    def with_minimal_translation_percent(self, minimal_percent: float) -> "Dataset":
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
        resource_language_stats[row.resource_info.resource][language] = (
            row.attributes.translated_strings
        )

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


def get_chart(
    chart_data: dict[str, Any],
    file_format: str = "png",
    width: int = 800,
    height: int = 800,
) -> bytes:
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
    return response.content


def minify_svg(data: bytes) -> bytes:
    return scour_string(
        data.decode("utf-8"), options=SimpleNamespace(strip_ids=True, shorten_ids=True)
    ).encode("utf-8")


def generate_diagram(
    dataset: Dataset,
    width: int,
    height: int,
    output: Path,
) -> None:
    chart_data = prepare_chart_data(dataset)
    file_format = output.suffix[1:]
    chart = get_chart(chart_data, file_format=file_format, width=width, height=height)

    if file_format == "svg":
        chart = minify_svg(chart)

    output.write_bytes(chart)
    logger.info(f"{output.name} chart file is saved")


def command_generate(
    output: Path,
    minimal_percent: int = 0,
    width: int = DEFAULT_WIDTH,
    height: int | None = None,
) -> None:
    logger.info(f"output: {output.resolve()}")
    output.parent.mkdir(exist_ok=True, parents=True)

    raw_data = get_translation_stats("o:dwarf-fortress-translation:p:dwarf-fortress-steam")
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
    command_generate(Path("diagrams") / "dwarf-fortress-steam.svg")


if __name__ == "__main__":
    main()
