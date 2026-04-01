from __future__ import annotations

import json
import os
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cyclistic")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
FIGURES_DIR = Path("figures")
MONTHS = [
    "202503",
    "202504",
    "202505",
    "202506",
    "202507",
    "202508",
    "202509",
    "202510",
    "202511",
    "202512",
    "202601",
    "202602",
]
USECOLS = [
    "ride_id",
    "rideable_type",
    "started_at",
    "ended_at",
    "start_station_name",
    "end_station_name",
    "member_casual",
]
CHUNK_SIZE = 250_000
ANALYSIS_START = pd.Timestamp("2025-03-01 00:00:00")
ANALYSIS_END = pd.Timestamp("2026-03-01 00:00:00")
RIDER_ORDER = ["casual", "member"]
DAY_ORDER = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_NAME_MAP = {
    1: "Sunday",
    2: "Monday",
    3: "Tuesday",
    4: "Wednesday",
    5: "Thursday",
    6: "Friday",
    7: "Saturday",
}
RIDER_PALETTE = {"casual": "#E76F51", "member": "#264653"}


@dataclass
class Metric:
    rides: int = 0
    ride_minutes: float = 0.0


def add_metric(store: dict, key: tuple, rides: int, ride_minutes: float) -> None:
    metric = store.setdefault(key, Metric())
    metric.rides += int(rides)
    metric.ride_minutes += float(ride_minutes)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def csv_member_name(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path) as archive:
        csv_members = [name for name in archive.namelist() if name.endswith(".csv") and not name.startswith("__MACOSX/")]
    if not csv_members:
        raise FileNotFoundError(f"No CSV found inside {zip_path}")
    return csv_members[0]


def build_metric_df(metric_store: dict, key_columns: list[str]) -> pd.DataFrame:
    rows = []
    for key, metric in metric_store.items():
        avg_minutes = metric.ride_minutes / metric.rides if metric.rides else 0.0
        rows.append(list(key) + [metric.rides, metric.ride_minutes, avg_minutes])
    return pd.DataFrame(rows, columns=key_columns + ["rides", "ride_minutes", "avg_ride_minutes"])


def aggregate_feature_counts(chunk: pd.DataFrame, metric_name: str, mask: pd.Series, store: dict) -> None:
    grouped = chunk.loc[mask].groupby(["month", "member_casual"]).size()
    for (month, rider), rides in grouped.items():
        store[(month, metric_name, rider)] += int(rides)


def plot_monthly_volume(month_df: pd.DataFrame, output_path: Path) -> None:
    # Ensure chronological order and pivot
    pivot_df = month_df.pivot(index="month", columns="member_casual", values="rides").fillna(0)
    pivot_df["total"] = pivot_df["casual"] + pivot_df["member"]
    pivot_df["casual_share_pct"] = (pivot_df["casual"] / pivot_df["total"] * 100)
    
    fig, ax1 = plt.subplots(figsize=(14, 8))
    x_positions = range(len(pivot_df))
    
    # Plotting Casual at the bottom (base) for direct share visualization
    ax1.bar(x_positions, pivot_df["casual"], label="casual", color=RIDER_PALETTE["casual"], alpha=0.9)
    ax1.bar(x_positions, pivot_df["member"], bottom=pivot_df["casual"], label="member", color=RIDER_PALETTE["member"], alpha=0.9)
    
    ax1.set_title("Strategic Window: Casual Riders Market Share Peaks in Summer", fontsize=20, fontweight="bold", pad=25)
    ax1.set_ylabel("Total Trips", fontsize=15, labelpad=10)
    ax1.set_xlabel("")
    ax1.set_xticks(list(x_positions))
    ax1.set_xticklabels(pivot_df.index, rotation=45, ha="right")
    
    # Legend matching stack order (Casual at bottom, Member on top)
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles[::-1], labels[::-1], title="Rider Type", loc="upper left", frameon=True)
    
    # Add share % labels on top of each bar for immediate insight
    for i, (month, row) in enumerate(pivot_df.iterrows()):
        total = row["total"]
        share = row["casual_share_pct"]
        ax1.text(i, total + (total * 0.01), f"{share:.1f}%", ha="center", va="bottom", 
                 fontsize=11, fontweight="bold", color=RIDER_PALETTE["casual"])

    # Secondary axis for the trend line
    ax2 = ax1.twinx()
    ax2.plot(list(x_positions), pivot_df["casual_share_pct"], 
             color="#2A9D8F", marker="D", linewidth=3, markersize=8, label="Casual Share Trend")
    ax2.set_ylabel("Casual Share of Total (%)", fontsize=14, color="#2A9D8F", labelpad=10)
    ax2.tick_params(axis="y", labelcolor="#2A9D8F")
    ax2.set_ylim(0, 55)
    ax2.grid(False) 
    
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def plot_grouped_bars(data: pd.DataFrame, x: str, y: str, title: str, ylabel: str, output_path: Path) -> None:
    plot_df = data.copy()
    if x == "day_of_week":
        plot_df[x] = pd.Categorical(plot_df[x], categories=DAY_ORDER, ordered=True)
        plot_df = plot_df.sort_values([x, "member_casual"])

    plt.figure(figsize=(11, 6))
    sns.barplot(data=plot_df, x=x, y=y, hue="member_casual", order=DAY_ORDER if x == "day_of_week" else None, palette=RIDER_PALETTE)
    plt.title(title)
    plt.xlabel("")
    plt.ylabel(ylabel)
    plt.legend(title="")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_hourly_lines(hour_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = hour_df.sort_values(["start_hour", "member_casual"])
    plt.figure(figsize=(11, 6))
    sns.lineplot(data=plot_df, x="start_hour", y="rides", hue="member_casual", marker="o", palette=RIDER_PALETTE, hue_order=RIDER_ORDER)
    plt.title("Ride Count by Start Hour")
    plt.xlabel("Hour of day")
    plt.ylabel("Trips")
    plt.xticks(range(0, 24, 1))
    plt.legend(title="")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_bike_type_mix(bike_type_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = bike_type_df.copy()
    plt.figure(figsize=(10, 6))
    sns.barplot(data=plot_df, x="rideable_type", y="ride_share_pct", hue="member_casual", palette=RIDER_PALETTE, hue_order=RIDER_ORDER)
    plt.title("Bike Type Mix by Rider Type")
    plt.xlabel("")
    plt.ylabel("Share of rides (%)")
    plt.legend(title="")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_heatmap(heatmap_df: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), sharey=True)
    for index, rider in enumerate(RIDER_ORDER):
        rider_df = heatmap_df.loc[heatmap_df["member_casual"] == rider].copy()
        pivot_df = rider_df.pivot(index="day_of_week", columns="start_hour", values="rides").reindex(DAY_ORDER).fillna(0)
        sns.heatmap(pivot_df, ax=axes[index], cmap="YlGnBu", cbar=index == 1, linewidths=0.2, linecolor="white")
        axes[index].set_title(f"{rider.capitalize()} usage pattern")
        axes[index].set_xlabel("Hour of day")
        axes[index].set_ylabel("")
    fig.suptitle("Weekly Usage Heatmap by Rider Type", fontsize=18)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_top_stations(top_stations_df: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), sharex=False)
    for index, rider in enumerate(RIDER_ORDER):
        rider_df = top_stations_df.loc[top_stations_df["member_casual"] == rider].sort_values("rides", ascending=True)
        sns.barplot(data=rider_df, x="rides", y="start_station_name", color=RIDER_PALETTE[rider], ax=axes[index])
        axes[index].set_title(f"Top start stations: {rider}")
        axes[index].set_xlabel("Trips")
        axes[index].set_ylabel("")
    fig.suptitle("Top Start Stations by Rider Type", fontsize=18)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="talk")

    overall_metrics: dict[tuple[str], Metric] = {}
    month_metrics: dict[tuple[str, str], Metric] = {}
    weekday_metrics: dict[tuple[int, str, str], Metric] = {}
    hour_metrics: dict[tuple[int, str], Metric] = {}
    bike_type_counts: dict[tuple[str, str], int] = defaultdict(int)
    station_counts: dict[tuple[str, str], int] = defaultdict(int)
    feature_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    heatmap_counts: dict[tuple[str, int, str], int] = defaultdict(int)
    max_ride_minutes: dict[str, float] = defaultdict(float)
    quality_rows: list[dict] = []

    for month_code in MONTHS:
        zip_path = RAW_DIR / f"{month_code}-divvy-tripdata.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Missing dataset: {zip_path}")

        quality = {
            "month": month_code,
            "source_file": zip_path.name,
            "rows_read": 0,
            "missing_datetime": 0,
            "invalid_member_type": 0,
            "out_of_scope_dates": 0,
            "nonpositive_duration": 0,
            "duration_over_24h": 0,
            "missing_start_station": 0,
            "missing_end_station": 0,
            "valid_rows": 0,
        }

        with zipfile.ZipFile(zip_path) as archive:
            csv_name = csv_member_name(zip_path)
            with archive.open(csv_name) as raw_file:
                reader = pd.read_csv(
                    raw_file,
                    usecols=USECOLS,
                    parse_dates=["started_at", "ended_at"],
                    chunksize=CHUNK_SIZE,
                    low_memory=False,
                )

                for chunk in reader:
                    quality["rows_read"] += len(chunk)

                    missing_datetime_mask = chunk["started_at"].isna() | chunk["ended_at"].isna()
                    quality["missing_datetime"] += int(missing_datetime_mask.sum())

                    valid_member_mask = chunk["member_casual"].isin(RIDER_ORDER)
                    quality["invalid_member_type"] += int((~valid_member_mask).sum())

                    chunk = chunk.loc[~missing_datetime_mask & valid_member_mask].copy()
                    if chunk.empty:
                        continue

                    in_scope_mask = chunk["started_at"].ge(ANALYSIS_START) & chunk["started_at"].lt(ANALYSIS_END)
                    quality["out_of_scope_dates"] += int((~in_scope_mask).sum())
                    chunk = chunk.loc[in_scope_mask].copy()
                    if chunk.empty:
                        continue

                    chunk["ride_length_min"] = (chunk["ended_at"] - chunk["started_at"]).dt.total_seconds() / 60

                    nonpositive_mask = chunk["ride_length_min"] <= 0
                    over_24h_mask = chunk["ride_length_min"] > 24 * 60
                    quality["nonpositive_duration"] += int(nonpositive_mask.sum())
                    quality["duration_over_24h"] += int(over_24h_mask.sum())

                    chunk = chunk.loc[~nonpositive_mask & ~over_24h_mask].copy()
                    if chunk.empty:
                        continue

                    chunk["month"] = chunk["started_at"].dt.strftime("%Y-%m")
                    chunk["day_of_week_num"] = ((chunk["started_at"].dt.dayofweek + 1) % 7) + 1
                    chunk["day_of_week"] = chunk["day_of_week_num"].map(DAY_NAME_MAP)
                    chunk["start_hour"] = chunk["started_at"].dt.hour
                    chunk["is_weekend"] = chunk["day_of_week_num"].isin([1, 7])
                    chunk["is_commute_window"] = (
                        chunk["day_of_week_num"].isin([2, 3, 4, 5, 6])
                        & (chunk["start_hour"].between(7, 9) | chunk["start_hour"].between(16, 18))
                    )
                    start_station_clean = chunk["start_station_name"].fillna("").str.strip()
                    end_station_clean = chunk["end_station_name"].fillna("").str.strip()
                    chunk["is_round_trip"] = start_station_clean.eq(end_station_clean) & start_station_clean.ne("")

                    quality["missing_start_station"] += int(start_station_clean.eq("").sum())
                    quality["missing_end_station"] += int(end_station_clean.eq("").sum())
                    quality["valid_rows"] += len(chunk)

                    grouped_overall = chunk.groupby("member_casual")["ride_length_min"].agg(["size", "sum", "max"])
                    for rider, row in grouped_overall.iterrows():
                        add_metric(overall_metrics, (rider,), int(row["size"]), float(row["sum"]))
                        max_ride_minutes[rider] = max(max_ride_minutes[rider], float(row["max"]))

                    grouped_month = chunk.groupby(["month", "member_casual"])["ride_length_min"].agg(["size", "sum"])
                    for (month_label, rider), row in grouped_month.iterrows():
                        add_metric(month_metrics, (month_label, rider), int(row["size"]), float(row["sum"]))

                    grouped_weekday = chunk.groupby(["day_of_week_num", "day_of_week", "member_casual"])["ride_length_min"].agg(["size", "sum"])
                    for (weekday_num, weekday_name, rider), row in grouped_weekday.iterrows():
                        add_metric(weekday_metrics, (int(weekday_num), weekday_name, rider), int(row["size"]), float(row["sum"]))

                    grouped_hour = chunk.groupby(["start_hour", "member_casual"])["ride_length_min"].agg(["size", "sum"])
                    for (start_hour, rider), row in grouped_hour.iterrows():
                        add_metric(hour_metrics, (int(start_hour), rider), int(row["size"]), float(row["sum"]))

                    grouped_heatmap = chunk.groupby(["day_of_week", "start_hour", "member_casual"]).size()
                    for (weekday_name, start_hour, rider), rides in grouped_heatmap.items():
                        heatmap_counts[(weekday_name, int(start_hour), rider)] += int(rides)

                    grouped_bike_type = chunk.groupby(["rideable_type", "member_casual"]).size()
                    for (rideable_type, rider), rides in grouped_bike_type.items():
                        bike_type_counts[(rideable_type, rider)] += int(rides)

                    grouped_stations = chunk.loc[start_station_clean.ne("")].groupby(["member_casual", "start_station_name"]).size()
                    for (rider, station_name), rides in grouped_stations.items():
                        station_counts[(rider, station_name)] += int(rides)

                    aggregate_feature_counts(chunk, "weekend_rides", chunk["is_weekend"], feature_counts)
                    aggregate_feature_counts(chunk, "commute_window_rides", chunk["is_commute_window"], feature_counts)
                    aggregate_feature_counts(chunk, "round_trip_rides", chunk["is_round_trip"], feature_counts)

        quality_rows.append(quality)

    overall_df = build_metric_df(overall_metrics, ["member_casual"]).sort_values("member_casual")
    overall_df["avg_ride_minutes"] = overall_df["avg_ride_minutes"].round(2)
    overall_df["total_ride_hours"] = (overall_df["ride_minutes"] / 60).round(2)
    overall_df["max_ride_minutes"] = overall_df["member_casual"].map(lambda rider: round(max_ride_minutes.get(rider, 0.0), 2))

    month_df = build_metric_df(month_metrics, ["month", "member_casual"]).sort_values(["month", "member_casual"])
    month_df["avg_ride_minutes"] = month_df["avg_ride_minutes"].round(2)

    weekday_df = build_metric_df(weekday_metrics, ["day_of_week_num", "day_of_week", "member_casual"]).sort_values(
        ["day_of_week_num", "member_casual"]
    )
    weekday_df["avg_ride_minutes"] = weekday_df["avg_ride_minutes"].round(2)

    hour_df = build_metric_df(hour_metrics, ["start_hour", "member_casual"]).sort_values(["start_hour", "member_casual"])
    hour_df["avg_ride_minutes"] = hour_df["avg_ride_minutes"].round(2)

    bike_type_df = pd.DataFrame(
        [
            {"rideable_type": rideable_type, "member_casual": rider, "rides": rides}
            for (rideable_type, rider), rides in bike_type_counts.items()
        ]
    ).sort_values(["rideable_type", "member_casual"])
    bike_totals = bike_type_df.groupby("member_casual")["rides"].transform("sum")
    bike_type_df["ride_share_pct"] = (bike_type_df["rides"] / bike_totals * 100).round(2)

    top_station_frames = []
    for rider in RIDER_ORDER:
        rider_station_df = pd.DataFrame(
            [
                {"member_casual": rider_type, "start_station_name": station_name, "rides": rides}
                for (rider_type, station_name), rides in station_counts.items()
                if rider_type == rider
            ]
        )
        if not rider_station_df.empty:
            top_station_frames.append(rider_station_df.sort_values("rides", ascending=False).head(10))
    top_stations_df = pd.concat(top_station_frames, ignore_index=True) if top_station_frames else pd.DataFrame()

    heatmap_df = pd.DataFrame(
        [
            {"day_of_week": weekday_name, "start_hour": start_hour, "member_casual": rider, "rides": rides}
            for (weekday_name, start_hour, rider), rides in heatmap_counts.items()
        ]
    )

    quality_df = pd.DataFrame(quality_rows).sort_values("month")

    feature_rows = []
    overall_rides_lookup = overall_df.set_index("member_casual")["rides"].to_dict()
    for (month_label, metric_name, rider), rides in sorted(feature_counts.items()):
        total_rides = overall_rides_lookup.get(rider, 0)
        feature_rows.append(
            {
                "month": month_label,
                "metric": metric_name,
                "member_casual": rider,
                "rides": rides,
                "share_of_total_rides_pct": round(rides / total_rides * 100, 2) if total_rides else 0.0,
            }
        )
    behavior_flags_df = pd.DataFrame(feature_rows)

    weekday_mode = (
        weekday_df.sort_values(["member_casual", "rides", "day_of_week_num"], ascending=[True, False, True])
        .drop_duplicates("member_casual")
        .set_index("member_casual")["day_of_week"]
        .to_dict()
    )
    overall_df["most_common_day_of_week"] = overall_df["member_casual"].map(weekday_mode)

    write_csv(overall_df, PROCESSED_DIR / "overall_summary.csv")
    write_csv(month_df, PROCESSED_DIR / "rides_by_month.csv")
    write_csv(weekday_df, PROCESSED_DIR / "rides_by_weekday.csv")
    write_csv(hour_df, PROCESSED_DIR / "rides_by_hour.csv")
    write_csv(bike_type_df, PROCESSED_DIR / "rides_by_bike_type.csv")
    write_csv(top_stations_df, PROCESSED_DIR / "top_start_stations.csv")
    write_csv(quality_df, PROCESSED_DIR / "data_quality_summary.csv")
    write_csv(behavior_flags_df, PROCESSED_DIR / "behavior_flags_summary.csv")

    key_metrics = {
        "analysis_window": {"start": "2025-03-01", "end": "2026-02-28", "months": len(MONTHS)},
        "overall_summary": overall_df.to_dict(orient="records"),
        "quality_totals": quality_df.sum(numeric_only=True).to_dict(),
    }
    (PROCESSED_DIR / "key_metrics.json").write_text(json.dumps(key_metrics, indent=2), encoding="utf-8")

    plot_monthly_volume(month_df, FIGURES_DIR / "monthly_ride_volume.png")
    plot_grouped_bars(weekday_df, "day_of_week", "rides", "Ride Count by Day of Week", "Trips", FIGURES_DIR / "rides_by_weekday.png")
    plot_grouped_bars(
        weekday_df,
        "day_of_week",
        "avg_ride_minutes",
        "Average Ride Length by Day of Week",
        "Average minutes",
        FIGURES_DIR / "avg_ride_length_by_weekday.png",
    )
    plot_hourly_lines(hour_df, FIGURES_DIR / "rides_by_hour.png")
    plot_bike_type_mix(bike_type_df, FIGURES_DIR / "bike_type_mix.png")
    if not heatmap_df.empty:
        plot_heatmap(heatmap_df, FIGURES_DIR / "usage_heatmap.png")
    if not top_stations_df.empty:
        plot_top_stations(top_stations_df, FIGURES_DIR / "top_stations_comparison.png")

    print("Cyclistic analysis artifacts generated.")


if __name__ == "__main__":
    main()
