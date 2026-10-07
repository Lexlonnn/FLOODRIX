"""Raw telemetry rainfall CSV -> model feature CSV.

Output cols: latitude,longitude,rainfall_1h,rainfall_6h,rainfall_24h,elevation,
             historical_flood_frequency,flood_zone,flood_occurred

Usage:
  python3 clean.py raw.csv out.csv [--floods floods.csv | --proxy] [--thresh 115]

floods.csv (optional, supply from SDMA/NDMA/news records): district,date
  date format DD-MM-YYYY. One row per district per flood day.
"""

import argparse
import json
import os
import urllib.request
import numpy as np
import pandas as pd

# Constants
RAIN = "Telemetry Hourly Rainfall (mm)"
TIME = "Data Acquisition Time"

LOW_ELEVATION_THRESH = 20.0
HIGH_FREQ_THRESH = 2
DEFAULT_RAIN_THRESH = 115.0

OUTPUT_COLUMNS = [
    "latitude",
    "longitude",
    "rainfall_1h",
    "rainfall_6h",
    "rainfall_24h",
    "elevation",
    "historical_flood_frequency",
    "flood_zone",
    "flood_occurred",
]


def fetch_elevation(lats, lons):
    """SRTM-derived elevation (m) from Open-Meteo, batches of 100. NaN on failure."""
    out = []
    for i in range(0, len(lats), 100):
        batch_lats = lats[i:i + 100]
        batch_lons = lons[i:i + 100]
        la = ",".join(f"{x:.5f}" for x in batch_lats)
        lo = ",".join(f"{x:.5f}" for x in batch_lons)
        url = f"https://api.open-meteo.com/v1/elevation?latitude={la}&longitude={lo}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FLOODRIX/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
                out.extend(data["elevation"])
        except Exception as e:
            print(f"Elevation fetch failed for batch {i//100 + 1}: {e}")
            out.extend([np.nan] * len(batch_lats))
    return out


def get_elevations(loc_df: pd.DataFrame, cache_path: str = "elevation_cache.csv") -> pd.DataFrame:
    """Fetch elevation for unique coordinates with CSV disk caching."""
    loc = loc_df[["Latitude", "Longitude"]].drop_duplicates().copy()
    cached = None
    if os.path.exists(cache_path):
        try:
            cached = pd.read_csv(cache_path)
            if {"Latitude", "Longitude", "elevation"}.issubset(cached.columns):
                cached = cached[["Latitude", "Longitude", "elevation"]].drop_duplicates()
            else:
                cached = None
        except Exception as e:
            print(f"Warning: Failed to read elevation cache ({e}), re-fetching...")
            cached = None

    if cached is not None:
        loc = loc.merge(cached, on=["Latitude", "Longitude"], how="left")
    else:
        loc["elevation"] = np.nan

    missing = loc[loc["elevation"].isna()]
    if not missing.empty:
        missing_lats = missing["Latitude"].tolist()
        missing_lons = missing["Longitude"].tolist()
        print(f"Fetching elevation for {len(missing_lats)} coordinates from Open-Meteo...")
        new_elevs = fetch_elevation(missing_lats, missing_lons)
        loc.loc[loc["elevation"].isna(), "elevation"] = new_elevs
        
        try:
            loc[["Latitude", "Longitude", "elevation"]].to_csv(cache_path, index=False)
            print(f"Cached {len(loc)} elevations to {cache_path}")
        except Exception as e:
            print(f"Warning: Failed to write elevation cache: {e}")
    else:
        print(f"Loaded {len(loc)} station elevations from cache '{cache_path}'")

    return loc


def main():
    ap = argparse.ArgumentParser(description="Raw telemetry rainfall CSV -> model feature CSV.")
    ap.add_argument("raw", help="Path to raw telemetry CSV")
    ap.add_argument("out", help="Path to output feature CSV")
    ap.add_argument("--floods", default=None, help="Path to real flood events CSV (columns: district,date)")
    ap.add_argument("--proxy", action="store_true", help="No flood records: label/frequency from rainfall_24h >= --thresh")
    ap.add_argument("--thresh", type=float, default=DEFAULT_RAIN_THRESH, help=f"Rainfall 24h threshold for proxy (default: {DEFAULT_RAIN_THRESH} mm)")
    ap.add_argument("--cache", default="elevation_cache.csv", help="Elevation cache CSV file path")
    a = ap.parse_args()

    # 1. Parse time & sort by Station, time
    print(f"Reading raw data from '{a.raw}'...")
    df = pd.read_csv(a.raw)
    df["District"] = df["District"].str.strip().str.upper().replace({"PALGHAT": "PALAKKAD"})
    df[TIME] = pd.to_datetime(df[TIME], format="%d-%m-%Y %H:%M")
    df[RAIN] = pd.to_numeric(df[RAIN], errors="coerce").fillna(0)
    df = df.sort_values(["Station", TIME]).reset_index(drop=True)

    # 2. Time-based rolling sums per station (window (t-h, t], missing time = 0 rain)
    print("Computing per-station rolling rainfall sums (1h, 6h, 24h)...")
    g = df.set_index(TIME).groupby("Station")[RAIN]
    for h in (1, 6, 24):
        df[f"rainfall_{h}h"] = g.rolling(f"{h}h").sum().values

    # 3. Elevation per unique station location with cache
    loc = get_elevations(df[["Latitude", "Longitude"]], cache_path=a.cache)
    df = df.merge(loc, on=["Latitude", "Longitude"], how="left")

    # 4. Flood labels and historical flood frequency
    df["_d"] = df[TIME].dt.normalize()

    if a.floods:
        print(f"Applying real flood events from '{a.floods}'...")
        ev = pd.read_csv(a.floods)
        ev.columns = [c.strip().lower() for c in ev.columns]
        ev["district"] = ev["district"].str.strip().str.upper().replace({"PALGHAT": "PALAKKAD"})
        ev["date"] = pd.to_datetime(ev["date"], format="%d-%m-%Y").dt.normalize()

        # historical_flood_frequency = distinct flood years per district
        freq = ev.groupby("district")["date"].apply(lambda s: s.dt.year.nunique())
        df["historical_flood_frequency"] = df["District"].map(freq).fillna(0).astype(int)

        # flood_occurred = 1 if district has flood on same day or next day, else 0
        same_day = ev[["district", "date"]].rename(columns={"district": "District", "date": "_d"})
        prev_day = ev[["district", "date"]].copy()
        prev_day["date"] = prev_day["date"] - pd.Timedelta(days=1)
        prev_day = prev_day.rename(columns={"district": "District", "date": "_d"})
        
        flood_days = pd.concat([same_day, prev_day]).drop_duplicates()
        flood_days["flood_occurred"] = 1

        df = df.merge(flood_days, on=["District", "_d"], how="left")
        df["flood_occurred"] = df["flood_occurred"].fillna(0).astype(int)

    elif a.proxy:
        print(f"Generating proxy flood labels using rainfall_24h >= {a.thresh} mm...")
        df["flood_occurred"] = (df["rainfall_24h"] >= a.thresh).astype(int)

        # Per station: count of distinct earlier days strictly before the row's date where flood_occurred was 1
        daily = df.groupby(["Station", "_d"])["flood_occurred"].max()
        prior = (daily.groupby(level=0).cumsum() - daily).rename("historical_flood_frequency")
        df = df.merge(prior, on=["Station", "_d"], how="left")
        df["historical_flood_frequency"] = df["historical_flood_frequency"].fillna(0).astype(int)

    else:
        print("\nWARNING: Neither --floods nor --proxy specified.")
        print("Label columns ('historical_flood_frequency', 'flood_occurred') will be empty.")
        df["historical_flood_frequency"] = np.nan
        df["flood_occurred"] = np.nan

    # 5. Flood zone: (elevation < 20) + (historical_flood_frequency >= 2), NaN only if elevation is NaN
    z = (df["elevation"] < LOW_ELEVATION_THRESH).astype(int) + (
        df["historical_flood_frequency"].fillna(0) >= HIGH_FREQ_THRESH
    ).astype(int)
    df["flood_zone"] = np.where(df["elevation"].isna(), np.nan, z)

    # 6. Assemble output in strict required order
    res = df.rename(columns={"Latitude": "latitude", "Longitude": "longitude"})[OUTPUT_COLUMNS]

    # Save to CSV
    print(f"Writing features to '{a.out}'...")
    res.to_csv(a.out, index=False)

    # 7. Print head(10) and summary
    print("\n--- First 10 Rows ---")
    print(res.head(10).to_string(index=False))

    print("\n" + "=" * 55)
    print("DATA PROCESSING SUMMARY")
    print("=" * 55)
    print(f"Total Rows: {len(res):,}")
    print("\nNaN Count per Column:")
    print(res.isna().sum().to_string())
    print("\nflood_occurred Value Counts:")
    print(res["flood_occurred"].value_counts(dropna=False).to_string())

    # Check for constant columns
    constant_cols = []
    for col in res.columns:
        valid_vals = res[col].dropna()
        if valid_vals.nunique() <= 1:
            val_repr = str(valid_vals.iloc[0]) if len(valid_vals) > 0 else "ALL NaN"
            constant_cols.append((col, val_repr))

    if constant_cols:
        print("\nWARNING: Constant or empty column(s) detected:")
        for col, val in constant_cols:
            print(f"  - '{col}' is constant with value: {val}")
    else:
        print("\nNo constant columns detected. All feature distributions are active.")
    print("=" * 55)


if __name__ == "__main__":
    main()