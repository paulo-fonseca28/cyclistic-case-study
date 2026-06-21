from __future__ import annotations

import json
import os
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-bikeshare")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

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
RIDER_PALETTE = {"casual": "#D55E00", "member": "#0072B2"}
ACCENT_COLOR = "#009E73"
CREATED_COLUMNS = [
    "ride_length_min",
    "month",
    "day_of_week_num",
    "day_of_week",
    "start_hour",
    "is_weekend",
    "is_commute_window",
    "is_round_trip",
]

REQUIRED_PROCESSED_COLUMNS = {
    "overall_summary.csv": {
        "member_casual",
        "rides",
        "ride_minutes",
        "avg_ride_minutes",
        "total_ride_hours",
        "max_ride_minutes",
        "most_common_day_of_week",
    },
    "rides_by_month.csv": {"month", "member_casual", "rides", "ride_minutes", "avg_ride_minutes"},
    "rides_by_weekday.csv": {
        "day_of_week_num",
        "day_of_week",
        "member_casual",
        "rides",
        "ride_minutes",
        "avg_ride_minutes",
    },
    "rides_by_hour.csv": {"start_hour", "member_casual", "rides", "ride_minutes", "avg_ride_minutes"},
    "rides_by_bike_type.csv": {"rideable_type", "member_casual", "rides", "ride_share_pct"},
    "top_start_stations.csv": {"member_casual", "rank", "start_station_name", "rides"},
    "data_quality_summary.csv": {
        "month",
        "source_file",
        "rows_read",
        "valid_rows",
        "rows_removed",
        "duplicate_ride_id",
        "missing_datetime",
        "invalid_member_type",
        "out_of_scope_dates",
        "nonpositive_duration",
        "duration_over_24h",
        "missing_start_station",
        "missing_end_station",
    },
    "behavior_flags_summary.csv": {
        "month",
        "metric",
        "member_casual",
        "rides",
        "share_of_monthly_rides_pct",
        "share_of_annual_rides_pct",
    },
    "rides_by_weekday_hour.csv": {"day_of_week", "start_hour", "member_casual", "rides"},
    "key_metrics.json": set(),
}
REQUIRED_REPORT_FILES = [
    REPORTS_DIR / "final_summary.md",
    TABLES_DIR / "executive_summary.csv",
    TABLES_DIR / "monthly_conversion_window.csv",
    TABLES_DIR / "top_station_segments.csv",
    TABLES_DIR / "data_quality_totals.csv",
    FIGURES_DIR / "monthly_ride_volume.png",
    FIGURES_DIR / "rides_by_weekday.png",
    FIGURES_DIR / "avg_ride_length_by_weekday.png",
    FIGURES_DIR / "rides_by_hour.png",
    FIGURES_DIR / "bike_type_mix.png",
    FIGURES_DIR / "usage_heatmap.png",
    FIGURES_DIR / "top_stations_comparison.png",
]


@dataclass
class Metric:
    rides: int = 0
    ride_minutes: float = 0.0


def configure_plot_style(context: str = "notebook") -> None:
    sns.set_theme(style="whitegrid", context=context)
    plt.rcParams.update(
        {
            "axes.titleweight": "bold",
            "axes.titlesize": 15,
            "axes.labelsize": 11,
            "figure.dpi": 110,
            "legend.frameon": False,
            "savefig.dpi": 180,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def ensure_output_dirs() -> None:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)


def csv_member_name(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path) as archive:
        csv_members = [
            name
            for name in archive.namelist()
            if name.endswith(".csv") and not name.startswith("__MACOSX/")
        ]
    if not csv_members:
        raise FileNotFoundError(f"No CSV found inside {zip_path}")
    return csv_members[0]


def raw_file_inventory() -> pd.DataFrame:
    rows = []
    for month in MONTHS:
        zip_path = RAW_DATA_DIR / f"{month}-divvy-tripdata.zip"
        row: dict[str, Any] = {
            "month": month,
            "source_file": zip_path.name,
            "exists": zip_path.exists(),
            "size_mb": round(zip_path.stat().st_size / 1024 / 1024, 2) if zip_path.exists() else 0.0,
            "csv_member": None,
        }
        if zip_path.exists() and zip_path.stat().st_size > 0:
            row["csv_member"] = csv_member_name(zip_path)
        rows.append(row)
    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def read_processed(filename: str) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing processed file: {path.relative_to(ROOT_DIR)}")
    return pd.read_csv(path)


def read_report_table(filename: str) -> pd.DataFrame:
    path = TABLES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing report table: {path.relative_to(ROOT_DIR)}")
    return pd.read_csv(path)


def add_metric(store: dict[tuple, Metric], key: tuple, rides: int, ride_minutes: float) -> None:
    metric = store.setdefault(key, Metric())
    metric.rides += int(rides)
    metric.ride_minutes += float(ride_minutes)


def build_metric_df(metric_store: dict[tuple, Metric], key_columns: list[str]) -> pd.DataFrame:
    rows = []
    for key, metric in metric_store.items():
        avg_minutes = metric.ride_minutes / metric.rides if metric.rides else 0.0
        rows.append(list(key) + [metric.rides, metric.ride_minutes, avg_minutes])
    return pd.DataFrame(rows, columns=key_columns + ["rides", "ride_minutes", "avg_ride_minutes"])


def aggregate_feature_counts(
    chunk: pd.DataFrame,
    metric_name: str,
    mask: pd.Series,
    store: dict[tuple[str, str, str], int],
) -> None:
    grouped = chunk.loc[mask].groupby(["month", "member_casual"]).size()
    for (month, rider), rides in grouped.items():
        store[(month, metric_name, rider)] += int(rides)


def mark_duplicate_ride_ids(chunk: pd.DataFrame, seen_ride_ids: set[str]) -> pd.Series:
    ride_ids = chunk["ride_id"].astype("string")
    duplicate_mask = ride_ids.isin(seen_ride_ids) | ride_ids.duplicated(keep="first")
    seen_ride_ids.update(ride_ids.dropna().unique().tolist())
    return duplicate_mask


def process_raw_data() -> dict[str, Any]:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    overall_metrics: dict[tuple[str], Metric] = {}
    month_metrics: dict[tuple[str, str], Metric] = {}
    weekday_metrics: dict[tuple[int, str, str], Metric] = {}
    hour_metrics: dict[tuple[int, str], Metric] = {}
    bike_type_counts: dict[tuple[str, str], int] = defaultdict(int)
    station_counts: dict[tuple[str, str], int] = defaultdict(int)
    feature_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    heatmap_counts: dict[tuple[str, int, str], int] = defaultdict(int)
    max_ride_minutes: dict[str, float] = defaultdict(float)
    quality_rows: list[dict[str, Any]] = []
    seen_ride_ids: set[str] = set()

    for month_code in MONTHS:
        zip_path = RAW_DATA_DIR / f"{month_code}-divvy-tripdata.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Missing dataset: {zip_path.relative_to(ROOT_DIR)}")

        quality = {
            "month": month_code,
            "source_file": zip_path.name,
            "rows_read": 0,
            "duplicate_ride_id": 0,
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

                    duplicate_mask = mark_duplicate_ride_ids(chunk, seen_ride_ids)
                    quality["duplicate_ride_id"] += int(duplicate_mask.sum())
                    chunk = chunk.loc[~duplicate_mask].copy()
                    if chunk.empty:
                        continue

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

                    grouped_weekday = chunk.groupby(["day_of_week_num", "day_of_week", "member_casual"])[
                        "ride_length_min"
                    ].agg(["size", "sum"])
                    for (weekday_num, weekday_name, rider), row in grouped_weekday.iterrows():
                        add_metric(
                            weekday_metrics,
                            (int(weekday_num), weekday_name, rider),
                            int(row["size"]),
                            float(row["sum"]),
                        )

                    grouped_hour = chunk.groupby(["start_hour", "member_casual"])["ride_length_min"].agg(
                        ["size", "sum"]
                    )
                    for (start_hour, rider), row in grouped_hour.iterrows():
                        add_metric(hour_metrics, (int(start_hour), rider), int(row["size"]), float(row["sum"]))

                    grouped_heatmap = chunk.groupby(["day_of_week", "start_hour", "member_casual"]).size()
                    for (weekday_name, start_hour, rider), rides in grouped_heatmap.items():
                        heatmap_counts[(weekday_name, int(start_hour), rider)] += int(rides)

                    grouped_bike_type = chunk.groupby(["rideable_type", "member_casual"]).size()
                    for (rideable_type, rider), rides in grouped_bike_type.items():
                        bike_type_counts[(rideable_type, rider)] += int(rides)

                    grouped_stations = chunk.loc[start_station_clean.ne("")].groupby(
                        ["member_casual", "start_station_name"]
                    ).size()
                    for (rider, station_name), rides in grouped_stations.items():
                        station_counts[(rider, station_name)] += int(rides)

                    aggregate_feature_counts(chunk, "weekend_rides", chunk["is_weekend"], feature_counts)
                    aggregate_feature_counts(chunk, "commute_window_rides", chunk["is_commute_window"], feature_counts)
                    aggregate_feature_counts(chunk, "round_trip_rides", chunk["is_round_trip"], feature_counts)

        quality_rows.append(quality)

    overall_df = build_metric_df(overall_metrics, ["member_casual"]).sort_values("member_casual")
    overall_df["avg_ride_minutes"] = overall_df["avg_ride_minutes"].round(2)
    overall_df["total_ride_hours"] = (overall_df["ride_minutes"] / 60).round(2)
    overall_df["max_ride_minutes"] = overall_df["member_casual"].map(
        lambda rider: round(max_ride_minutes.get(rider, 0.0), 2)
    )

    month_df = build_metric_df(month_metrics, ["month", "member_casual"]).sort_values(["month", "member_casual"])
    month_df["avg_ride_minutes"] = month_df["avg_ride_minutes"].round(2)

    weekday_df = build_metric_df(weekday_metrics, ["day_of_week_num", "day_of_week", "member_casual"]).sort_values(
        ["day_of_week_num", "member_casual"]
    )
    weekday_df["avg_ride_minutes"] = weekday_df["avg_ride_minutes"].round(2)

    hour_df = build_metric_df(hour_metrics, ["start_hour", "member_casual"]).sort_values(
        ["start_hour", "member_casual"]
    )
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
            top_rider_stations = rider_station_df.sort_values("rides", ascending=False).head(10).copy()
            top_rider_stations["rank"] = range(1, len(top_rider_stations) + 1)
            top_station_frames.append(top_rider_stations)
    top_stations_df = pd.concat(top_station_frames, ignore_index=True) if top_station_frames else pd.DataFrame()
    top_stations_df = top_stations_df[["member_casual", "rank", "start_station_name", "rides"]]

    heatmap_df = pd.DataFrame(
        [
            {"day_of_week": weekday_name, "start_hour": start_hour, "member_casual": rider, "rides": rides}
            for (weekday_name, start_hour, rider), rides in heatmap_counts.items()
        ]
    )
    heatmap_df["day_of_week"] = pd.Categorical(heatmap_df["day_of_week"], categories=DAY_ORDER, ordered=True)
    heatmap_df = heatmap_df.sort_values(["day_of_week", "start_hour", "member_casual"])

    quality_df = pd.DataFrame(quality_rows).sort_values("month")
    quality_df["rows_removed"] = quality_df["rows_read"] - quality_df["valid_rows"]
    quality_columns = [
        "month",
        "source_file",
        "rows_read",
        "valid_rows",
        "rows_removed",
        "duplicate_ride_id",
        "missing_datetime",
        "invalid_member_type",
        "out_of_scope_dates",
        "nonpositive_duration",
        "duration_over_24h",
        "missing_start_station",
        "missing_end_station",
    ]
    quality_df = quality_df[quality_columns]

    weekday_mode = (
        weekday_df.sort_values(["member_casual", "rides", "day_of_week_num"], ascending=[True, False, True])
        .drop_duplicates("member_casual")
        .set_index("member_casual")["day_of_week"]
        .to_dict()
    )
    overall_df["most_common_day_of_week"] = overall_df["member_casual"].map(weekday_mode)

    monthly_rides_lookup = month_df.set_index(["month", "member_casual"])["rides"].to_dict()
    annual_rides_lookup = overall_df.set_index("member_casual")["rides"].to_dict()
    feature_rows = []
    for (month_label, metric_name, rider), rides in sorted(feature_counts.items()):
        monthly_rides = monthly_rides_lookup.get((month_label, rider), 0)
        annual_rides = annual_rides_lookup.get(rider, 0)
        feature_rows.append(
            {
                "month": month_label,
                "metric": metric_name,
                "member_casual": rider,
                "rides": rides,
                "share_of_monthly_rides_pct": round(rides / monthly_rides * 100, 2) if monthly_rides else 0.0,
                "share_of_annual_rides_pct": round(rides / annual_rides * 100, 2) if annual_rides else 0.0,
            }
        )
    behavior_flags_df = pd.DataFrame(feature_rows)

    write_csv(overall_df, PROCESSED_DATA_DIR / "overall_summary.csv")
    write_csv(month_df, PROCESSED_DATA_DIR / "rides_by_month.csv")
    write_csv(weekday_df, PROCESSED_DATA_DIR / "rides_by_weekday.csv")
    write_csv(hour_df, PROCESSED_DATA_DIR / "rides_by_hour.csv")
    write_csv(bike_type_df, PROCESSED_DATA_DIR / "rides_by_bike_type.csv")
    write_csv(top_stations_df, PROCESSED_DATA_DIR / "top_start_stations.csv")
    write_csv(quality_df, PROCESSED_DATA_DIR / "data_quality_summary.csv")
    write_csv(behavior_flags_df, PROCESSED_DATA_DIR / "behavior_flags_summary.csv")
    write_csv(heatmap_df, PROCESSED_DATA_DIR / "rides_by_weekday_hour.csv")

    quality_totals = quality_df.sum(numeric_only=True).to_dict()
    key_metrics = {
        "analysis_window": {"start": "2025-03-01", "end": "2026-02-28", "months": len(MONTHS)},
        "source_files": [f"{month}-divvy-tripdata.zip" for month in MONTHS],
        "created_columns": CREATED_COLUMNS,
        "cleaning_rules": [
            "Drop duplicate ride_id records after the first occurrence.",
            "Drop records with missing start or end timestamps.",
            "Keep only member_casual values of casual or member.",
            "Keep rides started from 2025-03-01 through 2026-02-28.",
            "Drop rides with nonpositive duration.",
            "Drop rides longer than 24 hours.",
            "Preserve records with missing station names for time-based analysis; exclude blank stations from station rankings.",
        ],
        "overall_summary": overall_df.to_dict(orient="records"),
        "quality_totals": quality_totals,
    }
    (PROCESSED_DATA_DIR / "key_metrics.json").write_text(json.dumps(key_metrics, indent=2), encoding="utf-8")

    return key_metrics


def build_executive_summary() -> pd.DataFrame:
    overall = read_processed("overall_summary.csv")
    weekday = read_processed("rides_by_weekday.csv")
    hour = read_processed("rides_by_hour.csv")
    behavior = read_processed("behavior_flags_summary.csv")

    total_rides = overall["rides"].sum()
    summary = overall[["member_casual", "rides", "avg_ride_minutes", "most_common_day_of_week"]].copy()
    summary["ride_share_pct"] = (summary["rides"] / total_rides * 100).round(2)

    rides_by_rider = summary.set_index("member_casual")["rides"]
    weekend_counts = weekday.loc[weekday["day_of_week_num"].isin([1, 7])].groupby("member_casual")["rides"].sum()
    summary["weekend_ride_share_pct"] = (
        summary["member_casual"].map(weekend_counts).fillna(0) / summary["member_casual"].map(rides_by_rider) * 100
    ).round(2)

    behavior_counts = behavior.groupby(["metric", "member_casual"])["rides"].sum()
    for metric_name, output_column in [
        ("commute_window_rides", "commute_window_share_pct"),
        ("round_trip_rides", "round_trip_share_pct"),
    ]:
        if metric_name in behavior_counts.index.get_level_values("metric"):
            metric_counts = behavior_counts.xs(metric_name, level="metric")
        else:
            metric_counts = pd.Series(dtype=float)
        summary[output_column] = (
            summary["member_casual"].map(metric_counts).fillna(0)
            / summary["member_casual"].map(rides_by_rider)
            * 100
        ).round(2)

    top_hours = (
        hour.sort_values(["member_casual", "rides"], ascending=[True, False])
        .drop_duplicates("member_casual")
        .set_index("member_casual")["start_hour"]
    )
    summary["most_common_start_hour"] = summary["member_casual"].map(top_hours).astype(int)

    ordered_columns = [
        "member_casual",
        "rides",
        "ride_share_pct",
        "avg_ride_minutes",
        "most_common_day_of_week",
        "most_common_start_hour",
        "weekend_ride_share_pct",
        "commute_window_share_pct",
        "round_trip_share_pct",
    ]
    return summary[ordered_columns].sort_values("member_casual")


def build_monthly_conversion_window() -> pd.DataFrame:
    month = read_processed("rides_by_month.csv")
    rides = month.pivot(index="month", columns="member_casual", values="rides").fillna(0)
    avg_minutes = month.pivot(index="month", columns="member_casual", values="avg_ride_minutes").fillna(0)

    summary = pd.DataFrame(
        {
            "month": rides.index,
            "casual_rides": rides.get("casual", 0).astype(int).values,
            "member_rides": rides.get("member", 0).astype(int).values,
            "casual_avg_ride_minutes": avg_minutes.get("casual", 0).round(2).values,
            "member_avg_ride_minutes": avg_minutes.get("member", 0).round(2).values,
        }
    )
    summary["total_rides"] = summary["casual_rides"] + summary["member_rides"]
    summary["casual_share_pct"] = (summary["casual_rides"] / summary["total_rides"] * 100).round(2)
    summary["casual_to_member_duration_ratio"] = (
        summary["casual_avg_ride_minutes"] / summary["member_avg_ride_minutes"]
    ).round(2)
    return summary[
        [
            "month",
            "total_rides",
            "casual_rides",
            "member_rides",
            "casual_share_pct",
            "casual_avg_ride_minutes",
            "member_avg_ride_minutes",
            "casual_to_member_duration_ratio",
        ]
    ]


def build_top_station_segments() -> pd.DataFrame:
    stations = read_processed("top_start_stations.csv").copy()
    if "rank" not in stations.columns:
        stations = stations.sort_values(["member_casual", "rides"], ascending=[True, False])
        stations["rank"] = stations.groupby("member_casual").cumcount() + 1
    return stations[["member_casual", "rank", "start_station_name", "rides"]].sort_values(["member_casual", "rank"])


def build_quality_totals() -> pd.DataFrame:
    quality = read_processed("data_quality_summary.csv")
    totals = quality.sum(numeric_only=True).reset_index()
    totals.columns = ["metric", "value"]
    return totals


def save_figure(fig: plt.Figure, output_path: Path | None = None, close: bool = False) -> plt.Figure:
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=180, bbox_inches="tight")
    if close:
        plt.close(fig)
    return fig


def plot_monthly_volume(
    monthly_summary: pd.DataFrame,
    output_path: Path | None = None,
    close: bool = False,
) -> plt.Figure:
    fig, ax1 = plt.subplots(figsize=(12, 6.5))
    x_positions = range(len(monthly_summary))

    ax1.bar(
        x_positions,
        monthly_summary["casual_rides"],
        label="casual",
        color=RIDER_PALETTE["casual"],
        alpha=0.92,
    )
    ax1.bar(
        x_positions,
        monthly_summary["member_rides"],
        bottom=monthly_summary["casual_rides"],
        label="member",
        color=RIDER_PALETTE["member"],
        alpha=0.92,
    )
    ax1.set_title("Monthly ride volume and casual share")
    ax1.set_ylabel("Trips")
    ax1.set_xlabel("")
    ax1.set_xticks(list(x_positions))
    ax1.set_xticklabels(monthly_summary["month"], rotation=45, ha="right")
    ax1.ticklabel_format(style="plain", axis="y")
    ax1.legend(title="Rider type", loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(
        list(x_positions),
        monthly_summary["casual_share_pct"],
        color=ACCENT_COLOR,
        marker="o",
        linewidth=2.5,
        label="Casual share",
    )
    ax2.set_ylabel("Casual share of trips (%)", color=ACCENT_COLOR)
    ax2.tick_params(axis="y", labelcolor=ACCENT_COLOR)
    ax2.set_ylim(0, max(50, monthly_summary["casual_share_pct"].max() + 5))
    ax2.grid(False)

    fig.tight_layout()
    return save_figure(fig, output_path, close)


def plot_grouped_bars(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    ylabel: str,
    output_path: Path | None = None,
    close: bool = False,
) -> plt.Figure:
    plot_df = data.copy()
    if x == "day_of_week":
        plot_df[x] = pd.Categorical(plot_df[x], categories=DAY_ORDER, ordered=True)
        plot_df = plot_df.sort_values([x, "member_casual"])

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    sns.barplot(
        data=plot_df,
        x=x,
        y=y,
        hue="member_casual",
        order=DAY_ORDER if x == "day_of_week" else None,
        palette=RIDER_PALETTE,
        hue_order=RIDER_ORDER,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    ax.legend(title="")
    fig.tight_layout()
    return save_figure(fig, output_path, close)


def plot_hourly_lines(hour_df: pd.DataFrame, output_path: Path | None = None, close: bool = False) -> plt.Figure:
    plot_df = hour_df.sort_values(["start_hour", "member_casual"])
    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.lineplot(
        data=plot_df,
        x="start_hour",
        y="rides",
        hue="member_casual",
        marker="o",
        palette=RIDER_PALETTE,
        hue_order=RIDER_ORDER,
        ax=ax,
    )
    ax.set_title("Ride count by start hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Trips")
    ax.set_xticks(range(0, 24, 1))
    ax.ticklabel_format(style="plain", axis="y")
    ax.legend(title="")
    fig.tight_layout()
    return save_figure(fig, output_path, close)


def plot_bike_type_mix(
    bike_type_df: pd.DataFrame,
    output_path: Path | None = None,
    close: bool = False,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    sns.barplot(
        data=bike_type_df,
        x="rideable_type",
        y="ride_share_pct",
        hue="member_casual",
        palette=RIDER_PALETTE,
        hue_order=RIDER_ORDER,
        ax=ax,
    )
    ax.set_title("Bike type mix by rider type")
    ax.set_xlabel("")
    ax.set_ylabel("Share of rides (%)")
    ax.legend(title="")
    fig.tight_layout()
    return save_figure(fig, output_path, close)


def plot_heatmap(heatmap_df: pd.DataFrame, output_path: Path | None = None, close: bool = False) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(17, 7.5), sharey=True)
    for index, rider in enumerate(RIDER_ORDER):
        rider_df = heatmap_df.loc[heatmap_df["member_casual"] == rider].copy()
        pivot_df = (
            rider_df.pivot(index="day_of_week", columns="start_hour", values="rides")
            .reindex(DAY_ORDER)
            .reindex(columns=range(24), fill_value=0)
            .fillna(0)
        )
        sns.heatmap(
            pivot_df,
            ax=axes[index],
            cmap="YlGnBu",
            cbar=index == 1,
            linewidths=0.2,
            linecolor="white",
        )
        axes[index].set_title(f"{rider.capitalize()} usage pattern")
        axes[index].set_xlabel("Hour of day")
        axes[index].set_ylabel("")
    fig.suptitle("Weekly usage heatmap by rider type", fontsize=17, fontweight="bold")
    fig.tight_layout()
    return save_figure(fig, output_path, close)


def plot_top_stations(
    top_stations_df: pd.DataFrame,
    output_path: Path | None = None,
    close: bool = False,
) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.5), sharex=False)
    for index, rider in enumerate(RIDER_ORDER):
        rider_df = top_stations_df.loc[top_stations_df["member_casual"] == rider].sort_values(
            "rides", ascending=True
        )
        sns.barplot(data=rider_df, x="rides", y="start_station_name", color=RIDER_PALETTE[rider], ax=axes[index])
        axes[index].set_title(f"Top start stations: {rider}")
        axes[index].set_xlabel("Trips")
        axes[index].set_ylabel("")
        axes[index].ticklabel_format(style="plain", axis="x")
    fig.suptitle("Top start stations by rider type", fontsize=17, fontweight="bold")
    fig.tight_layout()
    return save_figure(fig, output_path, close)


def plot_data_quality_removals(
    quality_totals: pd.DataFrame,
    output_path: Path | None = None,
    close: bool = False,
) -> plt.Figure:
    reason_order = [
        "duplicate_ride_id",
        "missing_datetime",
        "invalid_member_type",
        "out_of_scope_dates",
        "nonpositive_duration",
        "duration_over_24h",
    ]
    plot_df = quality_totals.loc[quality_totals["metric"].isin(reason_order)].copy()
    plot_df["metric"] = pd.Categorical(plot_df["metric"], categories=reason_order, ordered=True)
    plot_df = plot_df.sort_values("metric")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.barplot(data=plot_df, x="value", y="metric", color="#666666", ax=ax)
    ax.set_title("Rows removed by cleaning rule")
    ax.set_xlabel("Rows")
    ax.set_ylabel("")
    ax.ticklabel_format(style="plain", axis="x")
    fig.tight_layout()
    return save_figure(fig, output_path, close)


def write_final_summary(
    executive_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    top_station_segments: pd.DataFrame,
    quality_totals: pd.DataFrame,
) -> None:
    executive = executive_summary.set_index("member_casual")
    casual = executive.loc["casual"]
    member = executive.loc["member"]
    peak_casual_share = monthly_summary.loc[monthly_summary["casual_share_pct"].idxmax()]
    peak_casual_volume = monthly_summary.loc[monthly_summary["casual_rides"].idxmax()]
    top_casual_stations = (
        top_station_segments.loc[top_station_segments["member_casual"] == "casual", "start_station_name"]
        .head(3)
        .tolist()
    )
    quality_lookup = quality_totals.set_index("metric")["value"].to_dict()

    duration_lift_pct = (casual["avg_ride_minutes"] / member["avg_ride_minutes"] - 1) * 100
    commute_gap = member["commute_window_share_pct"] - casual["commute_window_share_pct"]
    rows_removed = int(quality_lookup.get("rows_removed", 0))
    rows_read = int(quality_lookup.get("rows_read", 0))
    valid_rows = int(quality_lookup.get("valid_rows", 0))

    station_text = ", ".join(top_casual_stations)
    content = f"""# Bike-Share Rider Behavior Final Summary

## Business Task

The marketing team needs to understand how annual members and casual riders use bike-share trips differently so it can design strategies that convert casual riders into annual members.

## Data Scope

- Source data: 12 monthly Divvy trip files from March 2025 through February 2026.
- Rows read: {rows_read:,}
- Valid rows after cleaning: {valid_rows:,}
- Rows removed by cleaning rules: {rows_removed:,}
- Analysis unit: individual bike trips, not individual customers.

## Key Findings

1. Members account for {member['ride_share_pct']:.1f}% of valid rides, while casual riders account for {casual['ride_share_pct']:.1f}%.
2. Casual rides average {casual['avg_ride_minutes']:.2f} minutes, {duration_lift_pct:.1f}% longer than member rides at {member['avg_ride_minutes']:.2f} minutes.
3. Casual riders are more weekend-oriented: {casual['weekend_ride_share_pct']:.1f}% of casual rides occur on Saturday or Sunday, compared with {member['weekend_ride_share_pct']:.1f}% for members.
4. Members show a stronger commute pattern: their weekday commute-window share is {member['commute_window_share_pct']:.1f}%, {commute_gap:.1f} percentage points higher than casual riders.
5. Casual share peaks in {peak_casual_share['month']} at {peak_casual_share['casual_share_pct']:.1f}% of monthly rides, while casual ride volume peaks in {peak_casual_volume['month']} with {int(peak_casual_volume['casual_rides']):,} rides.
6. Top casual start stations include {station_text}, suggesting that lakefront, park, and visitor-oriented locations are important contexts for casual use.

## Recommendations

1. Launch seasonal conversion campaigns during the summer casual-riding window.
   - Evidence: casual share peaks in {peak_casual_share['month']} and casual volume peaks in {peak_casual_volume['month']}.
   - Action: promote annual membership upgrades in app, email, and paid digital channels from May through September.
   - Expected impact: higher conversion efficiency by concentrating spend when casual riders are most active.
   - Caveat: the trip data does not identify repeat individual riders, so targeting should use available app or transaction data if available.

2. Focus location-based messaging around the highest casual start stations.
   - Evidence: casual station leaders are concentrated around recognizable lakefront and visitor destinations such as {station_text}.
   - Action: use geotargeted digital ads, station signage, and QR-based offers near these locations.
   - Expected impact: reach casual riders close to the moment of recreational use, when the membership value proposition is concrete.
   - Caveat: station data is missing for some valid rides, so station rankings should not be treated as a full location census.

3. Position membership around repeated weekend and leisure convenience, not only commuting.
   - Evidence: casual rides are longer and more weekend-heavy than member rides.
   - Action: test messages that frame membership as a lower-friction way to ride repeatedly on weekends, paired with pass-to-membership upgrade credits.
   - Expected impact: connects the annual plan to the behavior casual riders already demonstrate.
   - Caveat: price sensitivity and customer intent are not available in the public trip data and should be validated with campaign tests or surveys.

## Limitations

- The dataset is anonymized and cannot connect trips to a single rider over time.
- The data does not include demographics, income, pricing plan history, marketing exposure, or conversion outcomes.
- Missing station names limit location analysis, although time-based patterns remain usable.
- Recommendations are directional and should be tested before large campaign investment.
"""
    (REPORTS_DIR / "final_summary.md").write_text(content, encoding="utf-8")


def create_report_assets(close_figures: bool = True) -> dict[str, Any]:
    ensure_output_dirs()
    configure_plot_style(context="talk")

    executive_summary = build_executive_summary()
    monthly_summary = build_monthly_conversion_window()
    top_station_segments = build_top_station_segments()
    quality_totals = build_quality_totals()

    write_csv(executive_summary, TABLES_DIR / "executive_summary.csv")
    write_csv(monthly_summary, TABLES_DIR / "monthly_conversion_window.csv")
    write_csv(top_station_segments, TABLES_DIR / "top_station_segments.csv")
    write_csv(quality_totals, TABLES_DIR / "data_quality_totals.csv")

    weekday = read_processed("rides_by_weekday.csv")
    hour = read_processed("rides_by_hour.csv")
    bike_type = read_processed("rides_by_bike_type.csv")
    heatmap = read_processed("rides_by_weekday_hour.csv")

    figures = {
        "monthly_ride_volume": plot_monthly_volume(
            monthly_summary, FIGURES_DIR / "monthly_ride_volume.png", close=close_figures
        ),
        "rides_by_weekday": plot_grouped_bars(
            weekday,
            "day_of_week",
            "rides",
            "Ride count by day of week",
            "Trips",
            FIGURES_DIR / "rides_by_weekday.png",
            close=close_figures,
        ),
        "avg_ride_length_by_weekday": plot_grouped_bars(
            weekday,
            "day_of_week",
            "avg_ride_minutes",
            "Average ride length by day of week",
            "Average minutes",
            FIGURES_DIR / "avg_ride_length_by_weekday.png",
            close=close_figures,
        ),
        "rides_by_hour": plot_hourly_lines(hour, FIGURES_DIR / "rides_by_hour.png", close=close_figures),
        "bike_type_mix": plot_bike_type_mix(bike_type, FIGURES_DIR / "bike_type_mix.png", close=close_figures),
        "usage_heatmap": plot_heatmap(heatmap, FIGURES_DIR / "usage_heatmap.png", close=close_figures),
        "top_stations_comparison": plot_top_stations(
            top_station_segments, FIGURES_DIR / "top_stations_comparison.png", close=close_figures
        ),
    }
    write_final_summary(executive_summary, monthly_summary, top_station_segments, quality_totals)

    return {
        "executive_summary": executive_summary,
        "monthly_summary": monthly_summary,
        "top_station_segments": top_station_segments,
        "quality_totals": quality_totals,
        "figures": figures,
    }


def validate_raw_files(errors: list[str]) -> None:
    for month in MONTHS:
        zip_path = RAW_DATA_DIR / f"{month}-divvy-tripdata.zip"
        if not zip_path.exists():
            errors.append(f"Missing raw file: {zip_path.relative_to(ROOT_DIR)}")
            continue
        if zip_path.stat().st_size == 0:
            errors.append(f"Raw file is empty: {zip_path.relative_to(ROOT_DIR)}")
            continue

        try:
            with zipfile.ZipFile(zip_path) as archive:
                csv_name = csv_member_name(zip_path)
                with archive.open(csv_name) as raw_file:
                    sample = pd.read_csv(raw_file, nrows=5)
        except (zipfile.BadZipFile, OSError, pd.errors.ParserError) as exc:
            errors.append(f"Cannot read {zip_path.relative_to(ROOT_DIR)}: {exc}")
            continue

        missing_columns = set(USECOLS) - set(sample.columns)
        if missing_columns:
            errors.append(
                f"{zip_path.relative_to(ROOT_DIR)} is missing columns: {', '.join(sorted(missing_columns))}"
            )


def read_required_csv(filename: str, errors: list[str]) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / filename
    if not path.exists():
        errors.append(f"Missing processed file: {path.relative_to(ROOT_DIR)}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    expected_columns = REQUIRED_PROCESSED_COLUMNS[filename]
    missing_columns = expected_columns - set(df.columns)
    if missing_columns:
        errors.append(f"{path.relative_to(ROOT_DIR)} is missing columns: {', '.join(sorted(missing_columns))}")
    if df.empty and filename != "key_metrics.json":
        errors.append(f"Processed file is empty: {path.relative_to(ROOT_DIR)}")
    return df


def validate_processed_files(errors: list[str]) -> None:
    for filename in REQUIRED_PROCESSED_COLUMNS:
        if filename.endswith(".json"):
            path = PROCESSED_DATA_DIR / filename
            if not path.exists():
                errors.append(f"Missing processed file: {path.relative_to(ROOT_DIR)}")
            continue
        read_required_csv(filename, errors)


def validate_processed_consistency(errors: list[str]) -> None:
    overall = read_required_csv("overall_summary.csv", errors)
    monthly = read_required_csv("rides_by_month.csv", errors)
    weekday = read_required_csv("rides_by_weekday.csv", errors)
    hourly = read_required_csv("rides_by_hour.csv", errors)
    bike_type = read_required_csv("rides_by_bike_type.csv", errors)
    quality = read_required_csv("data_quality_summary.csv", errors)
    behavior = read_required_csv("behavior_flags_summary.csv", errors)

    if any(df.empty for df in [overall, monthly, weekday, hourly, bike_type, quality, behavior]):
        return

    valid_riders = {"casual", "member"}
    for name, df in [
        ("overall_summary.csv", overall),
        ("rides_by_month.csv", monthly),
        ("rides_by_weekday.csv", weekday),
        ("rides_by_hour.csv", hourly),
        ("rides_by_bike_type.csv", bike_type),
        ("behavior_flags_summary.csv", behavior),
    ]:
        invalid_riders = set(df["member_casual"]) - valid_riders
        if invalid_riders:
            errors.append(f"{name} has invalid member_casual values: {', '.join(sorted(invalid_riders))}")

    valid_rows = int(quality["valid_rows"].sum())
    if int(overall["rides"].sum()) != valid_rows:
        errors.append("overall_summary.csv rides do not equal data_quality_summary.csv valid_rows")
    if int(monthly["rides"].sum()) != valid_rows:
        errors.append("rides_by_month.csv rides do not equal data_quality_summary.csv valid_rows")
    if int(weekday["rides"].sum()) != valid_rows:
        errors.append("rides_by_weekday.csv rides do not equal data_quality_summary.csv valid_rows")
    if int(hourly["rides"].sum()) != valid_rows:
        errors.append("rides_by_hour.csv rides do not equal data_quality_summary.csv valid_rows")

    removal_reason_columns = [
        "duplicate_ride_id",
        "missing_datetime",
        "invalid_member_type",
        "out_of_scope_dates",
        "nonpositive_duration",
        "duration_over_24h",
    ]
    rows_removed = int(quality["rows_removed"].sum())
    removal_reasons = int(quality[removal_reason_columns].sum().sum())
    if rows_removed != removal_reasons:
        errors.append("rows_removed does not equal the sum of documented removal reasons")

    if (overall["rides"] <= 0).any() or (overall["avg_ride_minutes"] <= 0).any():
        errors.append("overall_summary.csv contains nonpositive rides or average ride duration")
    if not monthly["month"].str.match(r"^20[0-9]{2}-[0-9]{2}$").all():
        errors.append("rides_by_month.csv contains invalid month labels")
    if not hourly["start_hour"].between(0, 23).all():
        errors.append("rides_by_hour.csv contains invalid start_hour values")
    if not behavior["share_of_monthly_rides_pct"].between(0, 100).all():
        errors.append("behavior_flags_summary.csv contains invalid monthly share percentages")


def validate_report_assets(errors: list[str]) -> None:
    for path in REQUIRED_REPORT_FILES:
        if not path.exists():
            errors.append(f"Missing report asset: {path.relative_to(ROOT_DIR)}")
        elif path.stat().st_size == 0:
            errors.append(f"Report asset is empty: {path.relative_to(ROOT_DIR)}")


def validate_project_outputs(raise_on_error: bool = True) -> list[str]:
    errors: list[str] = []
    validate_raw_files(errors)
    validate_processed_files(errors)
    validate_processed_consistency(errors)
    validate_report_assets(errors)
    if errors and raise_on_error:
        message = "Validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        raise SystemExit(message)
    return errors


def run_full_pipeline() -> dict[str, Any]:
    key_metrics = process_raw_data()
    report_assets = create_report_assets(close_figures=True)
    validate_project_outputs(raise_on_error=True)
    return {"key_metrics": key_metrics, "report_assets": report_assets}
