from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import httpx
from scour.scour import scourString as scour_string  # noqa: N813

if TYPE_CHECKING:
    from typing import Any

    from df_translation_stats.quickchart.models import Dataset


def minify_svg(data: bytes) -> bytes:
    return scour_string(data.decode("utf-8"), options=SimpleNamespace(strip_ids=True, shorten_ids=True)).encode("utf-8")


def prepare_chart_data(dataset: Dataset) -> dict[str, Any]:
    datasets = [
        dict(
            label=resource,
            data=[lines[label] for label in dataset.languages],
        )
        for resource, lines in dataset.data.items()
    ]

    return dict(
        type="horizontalBar",
        data=dict(labels=dataset.languages, datasets=datasets),
        options=dict(
            scales=dict(
                yAxes=[dict(stacked=True)],
                xAxes=[
                    dict(
                        stacked=True,
                        ticks=dict(
                            beginAtZero=True,
                            max=dataset.total_lines,
                            stepSize=10000,
                        ),
                    ),
                ],
            ),
        ),
    )


def get_chart(
    dataset: Dataset,
    file_format: str = "png",
    width: int = 800,
    height: int = 800,
) -> bytes:
    chart_data = prepare_chart_data(dataset)

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
