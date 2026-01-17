from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import TYPE_CHECKING

from langcodes import Language
from loguru import logger

from df_translation_stats.quickchart import Dataset, get_chart
from df_translation_stats.settings import settings
from df_translation_stats.stats.po_stats import PoStatsService

if TYPE_CHECKING:
    from pathlib import Path

    from df_translation_stats.stats import TranslationStats


def prepare_dataset(raw_data: TranslationStats, notranslate_tagged_strings: dict[str, int]) -> Dataset:
    languages: set[str] = set()
    total_lines_by_resource: dict[str, int] = {}
    resource_language_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in raw_data.data:
        language_code = row.resource_info.language_code
        if language_code == "en":
            continue

        language = Language.get(language_code).display_name()
        languages.add(language)
        resource = row.resource_info.resource
        total_lines_by_resource[resource] = max(
            total_lines_by_resource.get(resource, 0),
            row.attributes.total_strings,
        )
        resource_language_stats[resource][language] = max(
            row.attributes.translated_strings - notranslate_tagged_strings.get(resource, 0),
            0,
        )

    return Dataset(
        data=resource_language_stats,
        languages=list(languages),
        total_lines=sum(total_lines_by_resource.values()) - sum(notranslate_tagged_strings.values()),
    )


async def generate_diagram(
    dataset: Dataset,
    width: int,
    height: int,
    output_file: Path,
) -> None:
    file_format = output_file.suffix[1:]
    chart = await get_chart(dataset, file_format=file_format, width=width, height=height)
    output_file.write_bytes(chart)
    logger.info(f"{output_file.name} chart file is saved")


def calculate_height(dataset: Dataset) -> int:
    return (len(dataset.languages) + 6) * settings.diagram.line_height


async def one_diagram() -> None:
    input_path = settings.input_path
    assert input_path is not None
    assert input_path.exists()
    logger.info(f"input_path: {input_path.resolve()}")

    output_path = settings.output_path
    logger.info(f"output_path: {output_path.resolve()}")
    output_path.parent.mkdir(exist_ok=True, parents=True)

    service = PoStatsService(input_path)
    raw_data = await service.get_translation_stats()
    dataset: Dataset = prepare_dataset(raw_data, settings.notranslate_tagged_strings)

    logger.info(f"{dataset.resources=}")
    logger.info(f"{dataset.languages=}")
    logger.info(f"{dataset.total_lines=}")

    dataset = dataset.with_minimal_translation_percent(settings.minimal_translation_percent)
    count_by_language = dataset.get_count_by_languages()
    dataset.sort_languages()

    for language in dataset.languages:
        logger.info(f"{language}: {count_by_language[language] / dataset.total_lines * 100:.1f}%")

    height = calculate_height(dataset)
    await generate_diagram(dataset, settings.diagram.width, height, output_path)


if __name__ == "__main__":
    asyncio.run(one_diagram())
