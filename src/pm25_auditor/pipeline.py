from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold


LOGGER = logging.getLogger("pm25_auditor")


@dataclass
class AuditorOutputs:
    processed_files: Dict[str, Path]
    report_files: Dict[str, Path]
    figure_files: Dict[str, Path]


def setup_logging() -> None:
    if LOGGER.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def load_config(config_path: Path | str) -> dict:
    with open(config_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_directories(base_dir: Path, config: dict) -> dict:
    outputs = config["outputs"]
    processed_dir = base_dir / outputs["processed_dir"]
    figures_dir = base_dir / outputs["figures_dir"]
    reports_dir = base_dir / outputs["reports_dir"]
    for folder in [processed_dir, figures_dir, reports_dir]:
        folder.mkdir(parents=True, exist_ok=True)
    return {
        "processed_dir": processed_dir,
        "figures_dir": figures_dir,
        "reports_dir": reports_dir,
    }


def load_source_frames(base_dir: Path, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    sample_paths = config["sample_paths"]
    aqs_path = base_dir / sample_paths["aqs"]
    openaq_path = base_dir / sample_paths["openaq"]
    LOGGER.info("Loading sample AQS data from %s", aqs_path)
    LOGGER.info("Loading sample OpenAQ data from %s", openaq_path)
    return pd.read_csv(aqs_path), pd.read_csv(openaq_path)


def clean_aqs_daily(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["provider"] = "AQS"
    out["station_id"] = out["station_id"].astype(str)
    out["pollutant"] = "PM2.5"
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True).dt.tz_localize(None)
    out["timestamp_local"] = pd.to_datetime(out["timestamp_local"], errors="coerce").dt.tz_localize(None)
    out["date"] = out["timestamp_local"].dt.normalize()
    numeric_cols = ["value", "latitude", "longitude", "expected_count", "observed_count", "percent_complete"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["qa_flag"] = out["qa_flag"].fillna("none")
    return out.sort_values(["station_id", "timestamp_local"]).reset_index(drop=True)


def clean_openaq_daily(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["provider"] = "OpenAQ"
    out["station_id"] = out["station_id"].astype(str)
    out["pollutant"] = "PM2.5"
    out["timestamp_utc"] = pd.to_datetime(out["timestamp_utc"], errors="coerce", utc=True).dt.tz_localize(None)
    out["timestamp_local"] = pd.to_datetime(out["timestamp_local"], errors="coerce", utc=True).dt.tz_convert(None)
    out["date"] = out["timestamp_local"].dt.normalize()
    numeric_cols = ["value", "latitude", "longitude", "expected_count", "observed_count", "percent_complete"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["qa_flag"] = out["qa_flag"].fillna("none")
    return out.sort_values(["station_id", "timestamp_local"]).reset_index(drop=True)


UNIFIED_COLUMNS = [
    "provider",
    "station_id",
    "pair_id",
    "pollutant",
    "timestamp_utc",
    "timestamp_local",
    "date",
    "latitude",
    "longitude",
    "units",
    "value",
    "qa_flag",
    "expected_count",
    "observed_count",
    "percent_complete",
]


def combine_pm25_sources(aqs_df: pd.DataFrame, openaq_df: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat(
        [aqs_df[UNIFIED_COLUMNS].copy(), openaq_df[UNIFIED_COLUMNS].copy()],
        ignore_index=True,
    )
    # Coerce mixed timezone-aware and timezone-naive values into a single sortable dtype.
    combined["timestamp_utc"] = pd.to_datetime(combined["timestamp_utc"], errors="coerce", utc=True).dt.tz_localize(None)
    combined["timestamp_local"] = pd.to_datetime(
        combined["timestamp_local"], errors="coerce", utc=True
    ).dt.tz_localize(None)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce", utc=True).dt.tz_localize(None)
    combined = combined.drop_duplicates(subset=["provider", "station_id", "timestamp_local"])
    return combined.sort_values(["provider", "station_id", "timestamp_local"]).reset_index(drop=True)


def station_quality_metrics(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (provider, station_id), group in df.groupby(["provider", "station_id"]):
        group = group.dropna(subset=["date", "value"]).sort_values("date")
        if group.empty:
            continue
        unique_dates = group["date"].drop_duplicates().sort_values()
        expected_days = int((unique_dates.max() - unique_dates.min()).days + 1)
        observed_days = int(unique_dates.nunique())
        missing_rate = 1 - (observed_days / expected_days) if expected_days else np.nan
        q1 = group["value"].quantile(0.25)
        q3 = group["value"].quantile(0.75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        outliers = int(((group["value"] < low) | (group["value"] > high)).sum())
        records.append(
            {
                "provider": provider,
                "station_id": station_id,
                "start_date": unique_dates.min(),
                "end_date": unique_dates.max(),
                "observed_days": observed_days,
                "expected_days": expected_days,
                "missing_rate": round(missing_rate, 4),
                "mean_pm25": round(group["value"].mean(), 3),
                "std_pm25": round(group["value"].std(ddof=0), 3),
                "outlier_count": outliers,
                "outlier_rate": round(outliers / len(group), 4),
                "mean_percent_complete": round(group["percent_complete"].mean(), 3),
            }
        )
    return pd.DataFrame(records).sort_values(["provider", "station_id"]).reset_index(drop=True)


def build_coverage_summary(station_metrics: pd.DataFrame) -> pd.DataFrame:
    return (
        station_metrics.groupby("provider")
        .agg(
            station_count=("station_id", "nunique"),
            avg_missing_rate=("missing_rate", "mean"),
            avg_percent_complete=("mean_percent_complete", "mean"),
        )
        .reset_index()
    )


def build_data_quality_summary(df: pd.DataFrame, station_metrics: pd.DataFrame) -> pd.DataFrame:
    summaries = []
    for provider, group in df.groupby("provider"):
        summaries.append(
            {
                "provider": provider,
                "records": int(len(group)),
                "stations": int(group["station_id"].nunique()),
                "null_values": int(group["value"].isna().sum()),
                "flagged_records": int((group["qa_flag"] != "none").sum()),
                "avg_value": round(group["value"].mean(), 3),
                "avg_station_missing_rate": round(
                    station_metrics.loc[station_metrics["provider"] == provider, "missing_rate"].mean(), 4
                ),
            }
        )
    return pd.DataFrame(summaries)


def build_training_pairs(aqs_df: pd.DataFrame, openaq_df: pd.DataFrame) -> pd.DataFrame:
    aqs_pairs = aqs_df[["pair_id", "date", "station_id", "latitude", "longitude", "value"]].rename(
        columns={
            "station_id": "aqs_station_id",
            "latitude": "aqs_latitude",
            "longitude": "aqs_longitude",
            "value": "aqs_value",
        }
    )
    openaq_pairs = openaq_df[
        ["pair_id", "date", "station_id", "latitude", "longitude", "value", "percent_complete"]
    ].rename(
        columns={
            "station_id": "openaq_station_id",
            "latitude": "openaq_latitude",
            "longitude": "openaq_longitude",
            "value": "openaq_value",
        }
    )
    aqs_pairs["date"] = pd.to_datetime(aqs_pairs["date"], errors="coerce", utc=True).dt.tz_localize(None)
    openaq_pairs["date"] = pd.to_datetime(openaq_pairs["date"], errors="coerce", utc=True).dt.tz_localize(None)
    pairs = aqs_pairs.merge(openaq_pairs, on=["pair_id", "date"], how="inner")
    pairs["day_of_year"] = pd.to_datetime(pairs["date"]).dt.dayofyear
    pairs["lat_delta"] = (pairs["aqs_latitude"] - pairs["openaq_latitude"]).abs()
    pairs["lon_delta"] = (pairs["aqs_longitude"] - pairs["openaq_longitude"]).abs()
    return pairs.dropna().reset_index(drop=True)


def rmse(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def run_model_comparison(pairs: pd.DataFrame) -> pd.DataFrame:
    if pairs.empty or pairs["pair_id"].nunique() < 2:
        raise ValueError("Need at least two spatial groups in the training pairs to run grouped validation.")

    features = pairs[["openaq_value", "percent_complete", "day_of_year", "lat_delta", "lon_delta"]]
    target = pairs["aqs_value"]
    groups = pairs["pair_id"]
    cv = GroupKFold(n_splits=min(3, groups.nunique()))
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=200, random_state=42),
    }

    metrics = []
    for model_name, model in models.items():
        fold_rows = []
        for fold_id, (train_idx, test_idx) in enumerate(cv.split(features, target, groups=groups), start=1):
            X_train = features.iloc[train_idx]
            y_train = target.iloc[train_idx]
            X_test = features.iloc[test_idx]
            y_test = target.iloc[test_idx]
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            fold_rows.append(
                {
                    "model_name": model_name,
                    "fold": fold_id,
                    "rmse": rmse(y_test, preds),
                    "mae": mean_absolute_error(y_test, preds),
                    "r2": r2_score(y_test, preds),
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                }
            )

        fold_df = pd.DataFrame(fold_rows)
        metrics.append(
            {
                "model_name": model_name,
                "folds": int(len(fold_df)),
                "rmse_mean": round(fold_df["rmse"].mean(), 4),
                "mae_mean": round(fold_df["mae"].mean(), 4),
                "r2_mean": round(fold_df["r2"].mean(), 4),
                "n_train_total": int(fold_df["n_train"].sum()),
                "n_test_total": int(fold_df["n_test"].sum()),
            }
        )
    return pd.DataFrame(metrics).sort_values("rmse_mean").reset_index(drop=True)


def plot_monthly_mean(df: pd.DataFrame, output_path: Path) -> Path:
    monthly = (
        df.assign(month=pd.to_datetime(df["date"]).dt.month)
        .groupby(["provider", "month"])["value"]
        .mean()
        .reset_index()
    )
    plt.figure(figsize=(8, 5))
    for provider, group in monthly.groupby("provider"):
        plt.plot(group["month"], group["value"], marker="o", label=provider)
    plt.xlabel("Month")
    plt.ylabel("Mean PM2.5")
    plt.title("Monthly Mean PM2.5 by Provider")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    return output_path


def plot_station_map(df: pd.DataFrame, output_path: Path) -> Path:
    stations = df[["provider", "station_id", "latitude", "longitude"]].drop_duplicates()
    fig, ax = plt.subplots(figsize=(7, 7))
    for provider, group in stations.groupby("provider"):
        ax.scatter(group["longitude"], group["latitude"], label=provider, s=80)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("PM2.5 Monitor Locations")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def run_auditor(base_dir: Path | str, config_path: Path | str = "config.yaml") -> AuditorOutputs:
    setup_logging()
    base_dir = Path(base_dir)
    config = load_config(base_dir / config_path if not Path(config_path).is_absolute() else config_path)
    dirs = ensure_directories(base_dir, config)
    aqs_raw, openaq_raw = load_source_frames(base_dir, config)
    aqs_clean = clean_aqs_daily(aqs_raw)
    openaq_clean = clean_openaq_daily(openaq_raw)
    audit_table = combine_pm25_sources(aqs_clean, openaq_clean)
    station_metrics = station_quality_metrics(audit_table)
    coverage_summary = build_coverage_summary(station_metrics)
    data_quality_summary = build_data_quality_summary(audit_table, station_metrics)
    pairs = build_training_pairs(aqs_clean, openaq_clean)
    model_metrics = run_model_comparison(pairs)

    processed_files = {
        "aqs_clean": dirs["processed_dir"] / "aqs_clean.csv",
        "openaq_clean": dirs["processed_dir"] / "openaq_clean.csv",
        "audit_table": dirs["processed_dir"] / "audit_table.csv",
    }
    report_files = {
        "station_quality_metrics": dirs["reports_dir"] / "station_quality_metrics.csv",
        "coverage_summary": dirs["reports_dir"] / "coverage_summary.csv",
        "data_quality_summary": dirs["reports_dir"] / "data_quality_summary.csv",
        "model_metrics": dirs["reports_dir"] / "model_metrics.csv",
    }
    figure_files = {
        "monthly_mean": dirs["figures_dir"] / "monthly_mean_by_provider.png",
        "station_map": dirs["figures_dir"] / "station_map.png",
    }

    aqs_clean.to_csv(processed_files["aqs_clean"], index=False)
    openaq_clean.to_csv(processed_files["openaq_clean"], index=False)
    audit_table.to_csv(processed_files["audit_table"], index=False)
    station_metrics.to_csv(report_files["station_quality_metrics"], index=False)
    coverage_summary.to_csv(report_files["coverage_summary"], index=False)
    data_quality_summary.to_csv(report_files["data_quality_summary"], index=False)
    model_metrics.to_csv(report_files["model_metrics"], index=False)
    plot_monthly_mean(audit_table, figure_files["monthly_mean"])
    plot_station_map(audit_table, figure_files["station_map"])

    LOGGER.info("Auditor outputs written to %s", base_dir)
    return AuditorOutputs(
        processed_files=processed_files,
        report_files=report_files,
        figure_files=figure_files,
    )
