import json
import os
from pathlib import Path

import httpx
from loguru import logger

from .models import TranslationStats

TX_PROJECT_ID = "o:dwarf-fortress-translation:p:dwarf-fortress-steam"
CACHE_PATH = Path("cache.json")


def get_translation_stats(tx_token: str) -> TranslationStats:
    tx_token = os.getenv("TX_TOKEN")
    if not tx_token:
        if not CACHE_PATH.exists():
            msg = "No Transifex token found, nor cached data is available."
            raise ValueError(msg)

        logger.warning("No Transifex token found, using cached data.")
        return TranslationStats.model_validate_json(CACHE_PATH.read_text())

    url = "https://rest.api.transifex.com/resource_language_stats"
    headers = {"Authorization": f"Bearer {tx_token}"}
    response = httpx.get(url, params={"filter[project]": TX_PROJECT_ID}, headers=headers)

    response_text = response.text
    CACHE_PATH.write_text(json.dumps(response.json(), indent=4, ensure_ascii=False))
    return TranslationStats.model_validate_json(response_text)
