from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, NewType, cast

from babel.messages.pofile import read_po
from langcodes import Language

LanguageName = NewType("LanguageName", str)
ResourceName = NewType("ResourceName", str)


class StringWithContext(NamedTuple):
    string: str
    context: str | None


class CountTranslatedLinesResult(NamedTuple):
    total_lines_count: int
    translated_entries: set[StringWithContext]
    notranslated_entries: set[StringWithContext]


def count_translated_lines(path: Path) -> CountTranslatedLinesResult:
    entries: int = 0
    translated_entries: set[StringWithContext] = set()
    notranslated_entries: set[StringWithContext] = set()

    with path.open(encoding="utf-8") as file:
        catalog = read_po(file)
        for message in catalog:
            if message.id:
                entries += 1
                if message.string:
                    if message.string != message.id:
                        translated_entries.add(StringWithContext(cast(str, message.id), message.context))
                    else:
                        notranslated_entries.add(StringWithContext(cast(str, message.id), message.context))

    return CountTranslatedLinesResult(entries, translated_entries, notranslated_entries)


@dataclass
class ResourceStats:
    stats_per_language: dict[LanguageName, int]
    total_lines: int


def get_resource_stat(path: Path) -> ResourceStats:
    path = Path(path)
    stats_per_language: dict[LanguageName, int] = {}
    total_lines: int = 0
    all_notranslated: set[StringWithContext] = set()
    translated_items_per_language: dict[LanguageName, set[StringWithContext]] = {}

    for file in sorted(filter(Path.is_file, path.glob("*.po"))):
        language = LanguageName(Language.get(file.stem).display_name())
        translated_lines_info = count_translated_lines(file)
        translated_items_per_language[language] = translated_lines_info.translated_entries

        total_lines = max(total_lines, translated_lines_info.total_lines_count)


    for language, translated_items in translated_items_per_language.items():
        stats_per_language[language] = len(translated_items)

    return ResourceStats(stats_per_language, total_lines - len(all_notranslated))
