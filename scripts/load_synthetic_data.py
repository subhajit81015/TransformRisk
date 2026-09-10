from pathlib import Path
import sys

import pandas as pd


# ============================================================
# Project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.utils.db import engine


# ============================================================
# Synthetic data location
# ============================================================

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
)


# ============================================================
# Dataset mapping
# ============================================================

DATASETS = {
    "transformation_initiatives.csv":
        "transformation_initiatives",

    "transformation_risks.csv":
        "transformation_risks",

    "risk_controls.csv":
        "risk_controls",

    "mitigation_actions.csv":
        "mitigation_actions",

    "readiness_assessments.csv":
        "readiness_assessments",
}


# ============================================================
# Load one dataset
# ============================================================

def load_dataset(
    filename: str,
    table_name: str,
):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    df = pd.read_csv(path)

    if df.empty:
        raise RuntimeError(
            f"Dataset is empty: {path}"
        )

    df.to_sql(
        table_name,
        engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )

    print(
        f"{table_name}: "
        f"{len(df):,} rows loaded"
    )


# ============================================================
# Main
# ============================================================

def main():

    print(
        "Loading TransformRisk synthetic data..."
    )

    for filename, table_name in DATASETS.items():

        load_dataset(
            filename,
            table_name,
        )

    print(
        "\nSynthetic data loading complete."
    )


if __name__ == "__main__":
    main()
