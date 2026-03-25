"""
Cricsheet Data Downloader
Downloads T20 International match data from Cricsheet (JSON format)
"""

import os
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

# Cricsheet data URLs
CRICSHEET_URLS = {
    "t20i": "https://cricsheet.org/downloads/t20s_json.zip",
    "ipl": "https://cricsheet.org/downloads/ipl_json.zip",
    "bbl": "https://cricsheet.org/downloads/bbl_json.zip",
    "psl": "https://cricsheet.org/downloads/psl_json.zip",
    "cpl": "https://cricsheet.org/downloads/cpl_json.zip",
}

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> Path:
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    filename = url.split("/")[-1]
    file_path = dest_path / filename

    with open(file_path, "wb") as f:
        with tqdm(total=total_size, unit="B", unit_scale=True, desc=filename) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                pbar.update(len(chunk))

    return file_path


def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    """Extract a ZIP file."""
    folder_name = zip_path.stem  # Remove .zip extension
    extract_path = extract_to / folder_name
    extract_path.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    # Count extracted files
    json_files = list(extract_path.glob("*.json"))
    print(f"  Extracted {len(json_files)} JSON files to {extract_path}")

    return extract_path


def download_cricsheet_data(datasets: list[str] = None):
    """
    Download Cricsheet datasets.

    Args:
        datasets: List of dataset keys to download.
                  Default: ["t20i"] for T20 Internationals
    """
    if datasets is None:
        datasets = ["t20i"]  # Default to T20I for this project

    # Create data directory
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Cricsheet Data Downloader")
    print("=" * 60)

    for dataset_key in datasets:
        if dataset_key not in CRICSHEET_URLS:
            print(f"Unknown dataset: {dataset_key}")
            continue

        url = CRICSHEET_URLS[dataset_key]
        print(f"\nDownloading {dataset_key.upper()} dataset...")

        try:
            # Download ZIP
            zip_path = download_file(url, DATA_RAW)

            # Extract
            extract_zip(zip_path, DATA_RAW)

            # Optionally remove ZIP after extraction
            # zip_path.unlink()

        except requests.RequestException as e:
            print(f"  Error downloading {dataset_key}: {e}")
        except zipfile.BadZipFile as e:
            print(f"  Error extracting {dataset_key}: {e}")

    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"Data saved to: {DATA_RAW}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download Cricsheet data")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["t20i"],
        choices=list(CRICSHEET_URLS.keys()),
        help="Datasets to download (default: t20i)"
    )

    args = parser.parse_args()
    download_cricsheet_data(args.datasets)
