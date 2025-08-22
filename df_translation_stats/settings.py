from pathlib import Path
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)


class Settings(BaseSettings):
    tx_token: str | None = None

    diagram_width: int
    diagram_line_height: int

    notranslate_tagged_strings: dict[str, int] = Field(default_factory=dict)

    minimal_translation_percent: float

    output_dir: Path
    cache_path: Path | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        *_args,
        **_kwargs,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            EnvSettingsSource(settings_cls),
            DotEnvSettingsSource(settings_cls, env_file=".env"),
            TomlConfigSettingsSource(settings_cls, toml_file="config.toml"),
        )


settings = Settings()
