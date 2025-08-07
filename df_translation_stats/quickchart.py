from __future__ import annotations

from types import SimpleNamespace
from typing import Any
import httpx
from scour.scour import scourString as scour_string  # noqa: N813


def minify_svg(data: bytes) -> bytes:
    return scour_string(
        data.decode("utf-8"), options=SimpleNamespace(strip_ids=True, shorten_ids=True)
    ).encode("utf-8")


def get_chart(
    chart_data: dict[str, Any],
    file_format: str = "png",
    width: int = 800,
    height: int = 800,
) -> bytes:
    url = "https://quickchart.io/chart"
    payload = dict(
        width=width,
        height=height,
        backgroundColor="rgb(255, 255, 255)",
        format=file_format,
        chart=chart_data,
    )

    headers = {"Content-type": "application/json"}
    response = httpx.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    chart = response.content

    if file_format == "svg":
        chart = minify_svg(chart)

    return chart
