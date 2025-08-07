import os

import httpx
import rich
from dotenv import load_dotenv

from .models import TranslationStats

load_dotenv()


def get_translation_stats(project_id: str) -> TranslationStats:
    tx_token = os.getenv("TX_TOKEN")
    url = "https://rest.api.transifex.com/resource_language_stats"
    headers = {"Authorization": f"Bearer {tx_token}"}
    response = httpx.get(url, params={"filter[project]": project_id}, headers=headers)
    return TranslationStats.model_validate(response.json())


def main():
    result = get_translation_stats("o:dwarf-fortress-translation:p:dwarf-fortress-steam")
    rich.print(result)


if __name__ == "__main__":
    main()
