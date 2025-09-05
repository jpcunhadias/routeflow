from pathlib import Path

import pandas as pd


def standardize_trips(raw_root: Path, interim_root: Path, year="2023", month="01"):
    raw_path = raw_root / f"year={year}" / f"month={month}" / "trips.parquet"
    interim_dir = interim_root / f"year={year}" / f"month={month}"
    interim_dir.mkdir(parents=True, exist_ok=True)
    out_path = interim_dir / "trips.parquet"

    df = pd.read_parquet(raw_path)

    # Exemplos de colunas comuns no TLC (ajuste conforme yellow/green)
    # Pickup/Dropoff times:
    pickup_col = None
    dropoff_col = None
    for cand in ["tpep_pickup_datetime", "lpep_pickup_datetime", "pickup_datetime"]:
        if cand in df.columns:
            pickup_col = cand
            break
    for cand in ["tpep_dropoff_datetime", "lpep_dropoff_datetime", "dropoff_datetime"]:
        if cand in df.columns:
            dropoff_col = cand
            break

    if pickup_col is None or dropoff_col is None:
        raise ValueError(
            "Could not find pickup or dropoff datetime columns in the dataframe."
        )

    df["pickup_datetime"] = pd.to_datetime(df[pickup_col])
    df["dropoff_datetime"] = pd.to_datetime(df[dropoff_col])

    # Distância (milhas → km) — dependendo da coluna (trip_distance)
    dist_col = "trip_distance" if "trip_distance" in df.columns else None
    if dist_col:
        df["trip_distance_km"] = df[dist_col].astype("float32") * 1.60934
    else:
        df["trip_distance_km"] = None

    # Duração (min)
    df["duration_min"] = (
        df["dropoff_datetime"] - df["pickup_datetime"]
    ).dt.total_seconds() / 60.0

    # Time-derived
    df["hour"] = df["pickup_datetime"].dt.hour
    df["dow"] = df["pickup_datetime"].dt.dayofweek

    # Minimal schema
    keep = [
        "pickup_datetime",
        "dropoff_datetime",
        "trip_distance_km",
        "duration_min",
        "hour",
        "dow",
    ]
    out = df[keep].dropna(subset=["duration_min"]).reset_index(drop=True)
    out.to_parquet(out_path, index=False)
    print(f"[standardize] {out.shape} → {out_path}")
