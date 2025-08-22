
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource


class Settings(BaseSettings):
    model_config = SettingsConfigDict(toml_file="config.toml", env_file=".env")

    tx_token: str | None = None

    diagram_width: int
    diagram_line_height: int

    notranslate_tagged_strings: dict[str, int] = Field(default_factory=dict)

    minimal_tranlation_percent: float

    output_dir: Path
    cache_path: Path | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return env_settings, dotenv_settings, TomlConfigSettingsSource(settings_cls)


settings = Settings()
