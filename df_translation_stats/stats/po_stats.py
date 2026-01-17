from pathlib import Path
from typing import Any, NamedTuple, NewType, cast

from babel.messages.pofile import read_po

from df_translation_stats.stats.models import Attributes, ResourceInfo, ResourceLanguageStats, TranslationStats

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


def get_resource_stats(path: Path | str, translation_stats: TranslationStats) -> None:
    path = Path(path)
    assert path.exists()
    data = translation_stats.data

    for file in sorted(filter(Path.is_file, path.glob("*.po"))):
        translated_lines_info = count_translated_lines(file)
        resource_stat = ResourceLanguageStats(
            attributes=Attributes(
                total_strings=translated_lines_info.total_lines_count,
                translated_strings=len(translated_lines_info.translated_entries),
            ),
            resource_info=ResourceInfo(
                organization="dwarf-fortress-translation",
                project="dwarf-fortress-steam",
                resource=path.name,
                language_code=file.stem
            )
        )
        data.append(resource_stat)


class PoStatsService:
    path: Path

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    async def get_translation_stats(self) -> TranslationStats:
        translation_stats = TranslationStats(data=[])
        for resource_directory in sorted(filter(Path.is_dir, self.path.glob("*"))):
            get_resource_stats(resource_directory, translation_stats)
        return translation_stats

    async def get_resource_strings_tagged_notranslate(self, resource: str) -> list[dict[str, Any]]:
        raise NotImplemented
