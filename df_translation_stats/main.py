from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from langcodes import Language
from loguru import logger

from df_translation_stats.quickchart import Dataset, LanguageName, get_chart
from df_translation_stats.transifex import get_translation_stats

if TYPE_CHECKING:
    from df_translation_stats.transifex import TranslationStats

load_dotenv()

TX_TOKEN = os.getenv("TX_TOKEN")

DEFAULT_WIDTH = 600
DEFAULT_LINE_HEIGHT = 14


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


def one_diagram(
    output: Path = Path("diagrams") / "dwarf-fortress-steam.svg",
    minimal_percent: int = 0,
    width: int = DEFAULT_WIDTH,
    height: int | None = None,
) -> None:
    logger.info(f"output: {output.resolve()}")
    output.parent.mkdir(exist_ok=True, parents=True)

    raw_data = get_translation_stats(TX_TOKEN)
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


def two_diagrams(output_dir: Path = Path("diagrams")) -> None:
    logger.info(f"output_dir: {output_dir.resolve()}")
    output_dir.mkdir(exist_ok=True, parents=True)

    raw_data = get_translation_stats(TX_TOKEN)
    dataset: Dataset = prepare_dataset(raw_data)
    count_by_language = dataset.get_count_by_languages()

    logger.info(f"{dataset.resources=}")
    logger.info(f"{dataset.languages=}")
    logger.info(f"{dataset.total_lines=}")

    dataset.sort_languages()

    for language in dataset.languages:
        logger.info(f"{language}: {count_by_language[language] / dataset.total_lines * 100:.1f}%")

    width = DEFAULT_WIDTH
    height = (len(dataset.languages) + 6) * DEFAULT_LINE_HEIGHT
    generate_diagram(dataset, width, height, output_dir / "dwarf-fortress-steam.svg")

    dataset = dataset.with_minimal_translation_percent(1)
    height = (len(dataset.languages) + 6) * DEFAULT_LINE_HEIGHT
    generate_diagram(dataset, width, height, output_dir / "dwarf-fortress-steam-short.svg")


if __name__ == "__main__":
    one_diagram()
