# airflow/dags/vrp_pipeline.py
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG  # pyright: ignore[reportAttributeAccessIssue]
from airflow.operators.python import PythonOperator  # type: ignore

# permite importar módulos montados em /opt/airflow/src (via docker-compose)
sys.path.append("/opt/airflow/src")

logger = logging.getLogger(__name__)


def _parse_list(env_value: str | None, default_list: list[str]) -> list[str]:
    if env_value:
        return [x.strip() for x in env_value.split(",") if x.strip()]
    return default_list


def _validate_years(years: list[str]) -> None:
    for y in years:
        if not (len(y) == 4 and y.isdigit() and 1900 <= int(y) <= 2100):
            raise ValueError(f"Invalid year in NYC_TLC_YEARS: {y}")


def _validate_months(months: list[str]) -> None:
    valid = {f"{m:02d}" for m in range(1, 13)}
    for m in months:
        if m not in valid:
            raise ValueError(f"Invalid month in NYC_TLC_MONTHS: {m} (expected 01..12)")


def _validate_color(color: str) -> None:
    allowed = {"yellow", "green"}
    if color not in allowed:
        raise ValueError(
            f"Invalid NYC_TLC_COLOR: {color} (allowed: {', '.join(sorted(allowed))})"
        )


def _resolve_params() -> tuple[list[str], list[str], str]:
    years = _parse_list(os.getenv("NYC_TLC_YEARS"), ["2023"])
    months = _parse_list(os.getenv("NYC_TLC_MONTHS"), ["01", "02"])
    color = os.getenv("NYC_TLC_COLOR", "yellow").strip()

    _validate_years(years)
    _validate_months(months)
    _validate_color(color)

    logger.info("Resolved params -> years=%s months=%s color=%s", years, months, color)
    return years, months, color


def _download():
    from routeflow.datasets.nyc_tlc import (
        download_nyc_tlc,
        generate_nyc_tlc_urls,
    )

    years, months, color = _resolve_params()
    urls = generate_nyc_tlc_urls(years=years, months=months, color=color)

    raw_root = Path("/opt/airflow/data/raw/nyc_tlc")
    raw_root.mkdir(parents=True, exist_ok=True)

    logger.info("Starting download: %d files -> %s", len(urls), raw_root)
    download_nyc_tlc(raw_root, urls=urls)
    logger.info("Download finished.")


def _standardize():
    from routeflow.datasets.standardize_nyc import standardize_trips

    years, months, _ = _resolve_params()

    raw_root = Path("/opt/airflow/data/raw/nyc_tlc")
    interim_root = Path("/opt/airflow/data/interim/nyc_tlc")
    interim_root.mkdir(parents=True, exist_ok=True)

    for y in years:
        for m in months:
            logger.info("Standardizing year=%s month=%s", y, m)
            standardize_trips(raw_root, interim_root, year=y, month=m)
    logger.info("Standardization finished.")


default_args = {
    "owner": "routeflow",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="vrp_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,  # manual na demo
    catchup=False,
    tags=["routeflow", "vrp", "nyc-tlc"],
) as dag:
    download_nyc_tlc = PythonOperator(
        task_id="download_nyc_tlc",
        python_callable=_download,
        execution_timeout=timedelta(minutes=20),
    )

    standardize_trips = PythonOperator(
        task_id="standardize_trips",
        python_callable=_standardize,
        execution_timeout=timedelta(minutes=20),
    )

    download_nyc_tlc.set_downstream(standardize_trips)
