import json
from typing import Any

import httpx
from loguru import logger

from df_translation_stats.settings import settings
from df_translation_stats.transifex.models import TranslationStats

TX_PROJECT_ID = "o:dwarf-fortress-translation:p:dwarf-fortress-steam"


def get_translation_stats() -> TranslationStats:
    if not settings.tx_token:
        if not settings.cache_path.is_file():
            msg = "No Transifex token found, nor cached data is available."
            raise ValueError(msg)

        logger.warning("No Transifex token found, using cached data.")
        return TranslationStats.model_validate_json(settings.cache_path.read_text())

    url = "https://rest.api.transifex.com/resource_language_stats"
    headers = {"Authorization": f"Bearer {settings.tx_token}"}
    response = httpx.get(url, params={"filter[project]": TX_PROJECT_ID}, headers=headers)

    response_text = response.text
    settings.cache_path.write_text(json.dumps(response.json(), indent=4, ensure_ascii=False))
    return TranslationStats.model_validate_json(response_text)


def get_resource_strings_tagged_notranslate(resource: str) -> list[dict[str, Any]]:
    if not settings.tx_token:
        msg = "No Transifex token found."
        raise ValueError(msg)

    url = "https://rest.api.transifex.com/resource_strings"
    headers = {"Authorization": f"Bearer {settings.tx_token}"}
    response = httpx.get(url, params={
        "filter[resource]": f"{TX_PROJECT_ID}:r:{resource}",
        "filter[tags][all]": "notranslate",
    }, headers=headers)

    response_json = response.json()
    # settings.cache_path.write_text(json.dumps(response_json, indent=4, ensure_ascii=False))
    return response_json
