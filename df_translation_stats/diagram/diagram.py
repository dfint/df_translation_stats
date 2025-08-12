import matplotlib.pyplot as plt
from df_translation_stats.quickchart.quickchart import prepare_chart_data
import numpy as np

from df_translation_stats.quickchart.models import Dataset

COLORS = ["#4a79a4", "#f58c38", "#e3525a"]


def create_diagram(dataset: Dataset, width: int, height: int, file_name: str) -> None:
    chart_data = prepare_chart_data(dataset)
    data = chart_data["data"]
    languages = data["labels"]
    # languages.reverse()
    datasets = data["datasets"]

    fig, ax = plt.subplots()
    dpi = fig.dpi
    fig.set_figwidth(width / dpi)
    fig.set_figheight(height / dpi)

    # Build horizontal stacked bar chart
    bottom = np.zeros(len(languages))
    for dataset, color in zip(datasets, COLORS, strict=False):
        label = dataset["label"]
        series = dataset["data"]
        series.reverse()
        ax.barh(languages, series, left=bottom, label=label, color=color)
        bottom += np.array(series)

    # Make horizontal ticks light
    ax.tick_params(
        axis="x",
        colors="lightgray",
        length=4,
        width=0.8,
        labelcolor="black",
    )

    # Make vertical ticks light
    ax.tick_params(
        axis="y",
        length=0,
    )

    # Make border light
    for spine in ax.spines.values():
        spine.set_color("lightgray")

    # Add legend
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1), ncol=3, frameon=False)

    plt.tight_layout()

    fig.savefig(file_name)
