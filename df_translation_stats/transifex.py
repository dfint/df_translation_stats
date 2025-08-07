import os

import httpx

from .models import TranslationStats

TX_PROJECT_ID = "o:dwarf-fortress-translation:p:dwarf-fortress-steam"


def get_translation_stats(tx_token: str) -> TranslationStats:
    tx_token = os.getenv("TX_TOKEN")
    url = "https://rest.api.transifex.com/resource_language_stats"
    headers = {"Authorization": f"Bearer {tx_token}"}
    response = httpx.get(url, params={"filter[project]": TX_PROJECT_ID}, headers=headers)
    return TranslationStats.model_validate(response.json())
