import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd

DATASET_SLUG = "nilesh2042/airport-traffic-dataset"


def find_csv_file(folder: str) -> str | None:
    folder_path = Path(folder)
    if not folder_path.exists():
        return None

    csv_files = sorted(folder_path.glob("*.csv"))
    if not csv_files:
        return None

    return str(csv_files[0])


def download_dataset() -> str:
    download_dir = Path("data")
    download_dir.mkdir(exist_ok=True)

    if shutil.which("kaggle") is None:
        raise RuntimeError(
            "Kaggle CLI is not installed. Run: pip install kaggle\n"
            "Then configure ~/.kaggle/kaggle.json with your Kaggle credentials."
        )

    subprocess.run(
        [
            "kaggle",
            "datasets",
            "download",
            "-d",
            DATASET_SLUG,
            "-p",
            str(download_dir),
            "--unzip",
        ],
        check=True,
    )

    csv_path = find_csv_file(str(download_dir))
    if csv_path is None:
        raise FileNotFoundError("No CSV file was found in the downloaded dataset folder.")

    return csv_path


def load_airport_data() -> pd.DataFrame:
    local_path = os.environ.get("AIRPORT_DATA_PATH")
    if local_path and Path(local_path).exists():
        return pd.read_csv(local_path)

    csv_path = find_csv_file("data")
    if csv_path is None:
        csv_path = download_dataset()

    return pd.read_csv(csv_path)


def main() -> None:
    print("Loading airport traffic dataset...")

    try:
        df = load_airport_data()
    except Exception as exc:
        print(f"Could not load the Kaggle dataset: {exc}")
        print("\nTo use this script, either:")
        print("1. Put a CSV file in a local folder and set AIRPORT_DATA_PATH")
        print("2. Install Kaggle CLI and configure your Kaggle API credentials")
        return

    print("\nDataset preview:")
    print(df.head())
    print("\nShape:", df.shape)
    print("\nColumns:", list(df.columns))


if __name__ == "__main__":
    main()
