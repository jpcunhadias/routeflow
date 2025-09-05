from pathlib import Path

import pandas as pd


def generate_nyc_tlc_urls(years, months=None, color="yellow"):
    """
    Generates NYC TLC trip data URLs for given years and months.

    :param years: list of years (e.g., ["2023", "2024"])
    :param months: list of 2-digit months (e.g., ["01", "02", ...]); defaults to all 12 months
    :param color: "yellow" or "green"
    :return: list of tuples (year, month, url)
    """
    if months is None:
        months = [f"{m:02d}" for m in range(1, 13)]
    urls = []
    base = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    for year in years:
        for month in months:
            filename = f"{color}_tripdata_{year}-{month}.parquet"
            url = f"{base}/{filename}"
            urls.append((year, month, url))
    return urls


# Example: Yellow taxi data for 2023–2024 (all months)
NYC_TLC_URLS = generate_nyc_tlc_urls(years=["2023", "2024"], color="yellow")
# For green taxis, just switch the color argument:
# NYC_TLC_URLS = generate_nyc_tlc_urls(years=["2023", "2024"], color="green")


def download_nyc_tlc(dest_root: Path, urls=NYC_TLC_URLS):
    dest_root.mkdir(parents=True, exist_ok=True)
    for year, month, url in urls:
        out_dir = dest_root / f"year={year}" / f"month={month}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "trips.parquet"
        if out_path.exists():
            print(f"[skip] {out_path} já existe")
            continue
        print(f"[download] {url} → {out_path}")
        df = pd.read_parquet(url)
        df.to_parquet(out_path, index=False)
