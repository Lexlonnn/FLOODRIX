"""Generate a physically realistic synthetic flood dataset for Kerala road segments.

Used as a fallback when no external CSV is provided, and for reproducible offline
pipeline execution and CI testing.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

from ml.config import (
    DATA_RAW_DIR,
    RAW_DATA_FILE,
    RANDOM_SEED,
    KERALA_LAT_MIN,
    KERALA_LAT_MAX,
    KERALA_LON_MIN,
    KERALA_LON_MAX,
)

# Representative Kerala regions with realistic base coordinates and elevation profiles
REGIONS = [
    # (name, lat_center, lon_center, elev_min, elev_max, base_flood_freq, default_zone)
    ("Alappuzha-Kuttanad", 9.49, 76.33, 0.5, 3.5, 4.5, "high"),
    ("Kochi-Ernakulam", 9.98, 76.28, 2.0, 8.0, 3.8, "high"),
    ("Thrissur-Kole", 10.52, 76.21, 4.0, 15.0, 3.0, "medium"),
    ("Kottayam-Vembanad", 9.59, 76.52, 3.0, 18.0, 3.2, "medium"),
    ("Kozhikode-Urban", 11.25, 75.78, 5.0, 25.0, 2.5, "medium"),
    ("Thiruvananthapuram", 8.52, 76.93, 10.0, 45.0, 1.8, "low"),
    ("Palakkad-Gap", 10.78, 76.65, 60.0, 120.0, 1.2, "low"),
    ("Malappuram-Midland", 11.07, 76.07, 20.0, 70.0, 2.0, "medium"),
    ("Kannur-Coastal", 11.87, 75.37, 8.0, 35.0, 2.2, "medium"),
    ("Idukki-Highlands", 9.85, 76.98, 700.0, 1200.0, 1.5, "low"),
    ("Wayanad-Plateau", 11.68, 76.13, 650.0, 950.0, 2.2, "medium"),
]


def generate_synthetic_flood_data(
    num_samples: int = 5000,
    random_seed: int = RANDOM_SEED,
    output_path: Path = RAW_DATA_FILE,
) -> pd.DataFrame:
    """Generate synthetic Kerala flood dataset adhering strictly to schema rules."""
    np.random.seed(random_seed)

    records = []
    samples_per_region = int(np.ceil(num_samples / len(REGIONS)))

    for name, lat_c, lon_c, elev_min, elev_max, base_freq, def_zone in REGIONS:
        # Generate spatial cluster around region center
        lats = np.random.normal(loc=lat_c, scale=0.08, size=samples_per_region)
        lons = np.random.normal(loc=lon_c, scale=0.08, size=samples_per_region)

        # Clip within Kerala bounds
        lats = np.clip(lats, KERALA_LAT_MIN + 0.05, KERALA_LAT_MAX - 0.05)
        lons = np.clip(lons, KERALA_LON_MIN + 0.05, KERALA_LON_MAX - 0.05)

        # Elevation (log-normal / uniform blend)
        elevations = np.random.uniform(elev_min, elev_max, size=samples_per_region)
        elevations = np.maximum(elevations, 0.5)

        # Historical flood frequency
        hist_freq = np.random.poisson(lam=base_freq, size=samples_per_region)
        hist_freq = np.clip(hist_freq, 0, 12)

        # Rainfall synthesis: dry spells, moderate rains, monsoon cloudbursts
        # 24h rainfall (mix of light, moderate, heavy, deluge)
        weather_regime = np.random.choice(
            ["light", "moderate", "heavy", "deluge"],
            size=samples_per_region,
            p=[0.45, 0.30, 0.18, 0.07],
        )

        r24 = np.zeros(samples_per_region)
        for i, regime in enumerate(weather_regime):
            if regime == "light":
                r24[i] = np.random.uniform(0.0, 25.0)
            elif regime == "moderate":
                r24[i] = np.random.uniform(25.0, 75.0)
            elif regime == "heavy":
                r24[i] = np.random.uniform(75.0, 180.0)
            else:  # deluge / active monsoon depresssion
                r24[i] = np.random.uniform(180.0, 360.0)

        # 6h rainfall must satisfy 0 <= r6 <= r24
        share_6h = np.random.uniform(0.30, 0.85, size=samples_per_region)
        r6 = r24 * share_6h

        # 1h rainfall must satisfy 0 <= r1 <= r6
        share_1h = np.random.uniform(0.20, 0.70, size=samples_per_region)
        r1 = r6 * share_1h

        # Flood zone variations
        zone_probs = {
            "high": [0.1, 0.25, 0.65],
            "medium": [0.25, 0.55, 0.20],
            "low": [0.65, 0.25, 0.10],
        }[def_zone]
        zones = np.random.choice(["low", "medium", "high"], size=samples_per_region, p=zone_probs)

        # Physical latent risk calculation:
        # High rainfall + low elevation + high historical frequency + high zone -> flood
        zone_weight = np.array([{"low": 0.0, "medium": 0.8, "high": 1.6}[z] for z in zones])
        rain_24_scaled = r24 / 100.0
        rain_1_burst = (r1 / (r24 + 1e-4)) * 2.0
        elev_factor = np.exp(-elevations / 35.0)  # low elevations high risk
        hist_factor = hist_freq * 0.22

        latent_score = (
            -4.5
            + 1.8 * rain_24_scaled
            + 0.9 * rain_1_burst
            + 2.1 * elev_factor
            + hist_factor
            + zone_weight
            + np.random.normal(0, 0.35, size=samples_per_region)
        )

        # Sigmoid to get probability of historical occurrence
        prob = 1.0 / (1.0 + np.exp(-latent_score))
        occurred = (np.random.uniform(0, 1, size=samples_per_region) < prob).astype(int)

        for j in range(samples_per_region):
            records.append({
                "latitude": round(float(lats[j]), 6),
                "longitude": round(float(lons[j]), 6),
                "rainfall_1h": round(float(r1[j]), 2),
                "rainfall_6h": round(float(r6[j]), 2),
                "rainfall_24h": round(float(r24[j]), 2),
                "elevation": round(float(elevations[j]), 1),
                "historical_flood_frequency": int(hist_freq[j]),
                "flood_zone": str(zones[j]),
                "flood_occurred": int(occurred[j]),
            })

    df = pd.DataFrame(records).iloc[:num_samples]

    # Enforce rainfall monotonic constraint strictly: 1h <= 6h <= 24h
    df["rainfall_6h"] = np.maximum(df["rainfall_6h"], df["rainfall_1h"])
    df["rainfall_24h"] = np.maximum(df["rainfall_24h"], df["rainfall_6h"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    pos_rate = df["flood_occurred"].mean()
    print(f"Generated synthetic dataset at {output_path} with {len(df)} rows.")
    print(f"Positive flood occurrence rate: {pos_rate:.2%} ({df['flood_occurred'].sum()} positives)")

    return df


if __name__ == "__main__":
    generate_synthetic_flood_data()
