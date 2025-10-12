from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from langcodes import Language
from loguru import logger

from df_translation_stats.quickchart import Dataset, LanguageName, get_chart
from df_translation_stats.transifex import get_translation_stats, get_resource_strings_tagged_notranslate
from df_translation_stats.settings import settings

if TYPE_CHECKING:
    from df_translation_stats.transifex import TranslationStats


def get_notranslate_tagged_strings_count(resources: list[str]) -> dict[str, int]:
    result = dict()
    for resource in resources:
        result[resource] = len(get_resource_strings_tagged_notranslate(resource))
    return result


def prepare_dataset(raw_data: TranslationStats) -> Dataset:
    languages: set[LanguageName] = set()
    total_lines_by_resource: dict[str, int] = {}
    resource_language_stats = defaultdict(lambda: defaultdict(int))

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
            row.attributes.translated_strings - settings.notranslate_tagged_strings.get(resource, 0),
            0,
        )

    return Dataset(
        data=resource_language_stats,
        languages=languages,
        total_lines=sum(total_lines_by_resource.values()) - sum(settings.notranslate_tagged_strings.values()),
    )


def generate_diagram(
    dataset: Dataset,
    width: int,
    height: int,
    output_file: Path,
) -> None:
    file_format = output_file.suffix[1:]
    chart = get_chart(dataset, file_format=file_format, width=width, height=height)
    output_file.write_bytes(chart)
    logger.info(f"{output_file.name} chart file is saved")


def calculate_height(dataset: Dataset) -> int:
    return (len(dataset.languages) + 6) * settings.diagram.line_height


def one_diagram() -> None:
    output = settings.output_path
    logger.info(f"output: {output.resolve()}")
    output.parent.mkdir(exist_ok=True, parents=True)

    raw_data = get_translation_stats()
    dataset: Dataset = prepare_dataset(raw_data)
    count_by_language = dataset.get_count_by_languages()

    logger.info(f"{dataset.resources=}")
    logger.info(f"{dataset.languages=}")
    logger.info(f"{dataset.total_lines=}")

    dataset = dataset.with_minimal_translation_percent(settings.minimal_translation_percent)

    dataset.sort_languages()

    for language in dataset.languages:
        logger.info(f"{language}: {count_by_language[language] / dataset.total_lines * 100:.1f}%")

    height = calculate_height(dataset)
    generate_diagram(dataset, settings.diagram.width, height, output)


if __name__ == "__main__":
    one_diagram()
