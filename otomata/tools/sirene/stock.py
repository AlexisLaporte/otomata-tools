"""
Batch operations using local SIRENE stock file (offline mode).

The stock file contains all French establishments (~35M records, ~2GB parquet).
Much faster than API for batch processing thousands of companies.

Usage:
    from otomata.tools.sirene import SireneStock

    stock = SireneStock()

    # Download stock file first (~2GB, takes a few minutes)
    stock.download()

    # Then use for batch enrichment
    addresses = stock.get_headquarters_addresses(["443061841", "552032534"])

Storage:
    Default location: ~/.otomata/sirene/StockEtablissement.parquet
    Override with: SireneStock(data_dir="/custom/path")
"""

import threading
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

from ...config import get_config_dir

# Storage location
DEFAULT_DATA_DIR = get_config_dir() / "sirene"
STOCK_FILENAME = "StockEtablissement.parquet"
LOCK_FILENAME = ".download.lock"

# data.gouv.fr dataset
DATASET_URL = "https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/"
STOCK_DOWNLOAD_URL = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet"

COLUMNS = [
    "siren",
    "siret",
    "etablissementSiege",
    "etatAdministratifEtablissement",
    "numeroVoieEtablissement",
    "typeVoieEtablissement",
    "libelleVoieEtablissement",
    "codePostalEtablissement",
    "libelleCommuneEtablissement",
    "coordonneeLambertAbscisseEtablissement",
    "coordonneeLambertOrdonneeEtablissement",
]

# Global lock for download
_download_lock = threading.Lock()
_download_in_progress = False


class SireneStock:
    """
    Batch operations using local SIRENE stock file.

    The stock file must be downloaded before use. Call stock.download()
    or use the CLI: otomata sirene stock download

    Example:
        stock = SireneStock()
        stock.download()  # First time only, ~2GB

        addresses = stock.get_headquarters_addresses(["443061841"])
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        auto_sync: bool = False,
        max_age_days: int = 30,
    ):
        """
        Initialize stock handler.

        Args:
            data_dir: Directory to store stock file (default: ~/.otomata/sirene)
            auto_sync: Auto-download if missing, or async update if outdated
            max_age_days: Max file age before triggering async update (default: 30)
        """
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.stock_file = self.data_dir / STOCK_FILENAME
        self.lock_file = self.data_dir / LOCK_FILENAME
        self.auto_sync = auto_sync
        self.max_age_days = max_age_days

    def download(self, force: bool = False, async_mode: bool = False) -> Optional[Path]:
        """
        Download or update stock file from data.gouv.fr.

        Args:
            force: Re-download even if file exists
            async_mode: Run download in background thread

        Returns:
            Path to downloaded file (None if async)
        """
        if async_mode:
            thread = threading.Thread(
                target=self._download_sync, args=(force,), daemon=True
            )
            thread.start()
            return None
        return self._download_sync(force)

    def _download_sync(self, force: bool = False) -> Path:
        """Synchronous download implementation."""
        global _download_in_progress
        import requests

        with _download_lock:
            if _download_in_progress:
                print("Download already in progress, skipping...")
                return self.stock_file
            _download_in_progress = True

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.lock_file.write_text(str(time.time()))

            if self.stock_file.exists() and not force:
                size_gb = self.stock_file.stat().st_size / 1e9
                print(f"Stock file exists: {self.stock_file} ({size_gb:.1f} GB)")
                print("Use download(force=True) to re-download")
                return self.stock_file

            print(f"Downloading SIRENE stock file (~2GB)...")
            print(f"Source: {STOCK_DOWNLOAD_URL}")
            print(f"Destination: {self.stock_file}")

            temp_file = self.stock_file.with_suffix(".parquet.tmp")

            response = requests.get(STOCK_DOWNLOAD_URL, stream=True, timeout=3600)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        print(
                            f"\rProgress: {pct:.1f}% ({downloaded / 1e9:.2f} GB)",
                            end="",
                            flush=True,
                        )

            print(f"\nDownload complete, replacing old file...")
            temp_file.replace(self.stock_file)
            print(f"Stock file ready: {self.stock_file}")
            return self.stock_file

        except Exception as e:
            print(f"Download error: {e}")
            temp_file = self.stock_file.with_suffix(".parquet.tmp")
            if temp_file.exists():
                temp_file.unlink()
            raise

        finally:
            if self.lock_file.exists():
                self.lock_file.unlink()
            with _download_lock:
                _download_in_progress = False

    @property
    def is_downloading(self) -> bool:
        """Check if a download is currently in progress."""
        global _download_in_progress
        if _download_in_progress:
            return True
        if self.lock_file.exists():
            try:
                lock_time = float(self.lock_file.read_text())
                if time.time() - lock_time > 7200:  # 2 hours
                    self.lock_file.unlink()
                    return False
                return True
            except Exception:
                return False
        return False

    @property
    def is_available(self) -> bool:
        """Check if stock file is downloaded and ready."""
        return self.stock_file.exists()

    @property
    def file_size_gb(self) -> Optional[float]:
        """Get stock file size in GB, or None if not downloaded."""
        if self.stock_file.exists():
            return self.stock_file.stat().st_size / 1e9
        return None

    @property
    def file_age_days(self) -> Optional[float]:
        """Get stock file age in days, or None if not downloaded."""
        if self.stock_file.exists():
            mtime = self.stock_file.stat().st_mtime
            return (time.time() - mtime) / 86400
        return None

    def _ensure_file(self):
        """Ensure stock file exists."""
        if self.auto_sync:
            self._maybe_sync()

        if not self.stock_file.exists():
            raise FileNotFoundError(
                f"Stock file not found: {self.stock_file}\n"
                f"Download it first:\n"
                f"  - CLI: otomata sirene stock download\n"
                f"  - Python: stock.download()\n"
                f"  - Manual: {DATASET_URL}"
            )

    def _maybe_sync(self):
        """Check if sync needed and trigger async download if outdated."""
        if self.is_downloading:
            return

        if not self.stock_file.exists():
            print("Stock file missing, downloading...")
            self.download()
            return

        age = self.file_age_days
        if age and age > self.max_age_days:
            print(f"Stock file is {age:.0f} days old, starting background update...")
            self.download(force=True, async_mode=True)

    def _query_parquet(
        self, filters: List[tuple], columns: Optional[List[str]] = None
    ) -> "pd.DataFrame":
        """
        Query parquet file with filters - memory efficient.

        Uses pyarrow to filter at read time, only loading matching rows.
        """
        import pyarrow.parquet as pq
        import pyarrow.compute as pc

        self._ensure_file()

        cols = columns or COLUMNS
        table = pq.read_table(self.stock_file, columns=cols)

        mask = None
        for col, op, value in filters:
            if op == "==":
                col_mask = pc.equal(table[col], value)
            elif op == "in":
                col_mask = pc.is_in(table[col], value_set=value)
            else:
                raise ValueError(f"Unsupported operator: {op}")

            if mask is None:
                mask = col_mask
            else:
                mask = pc.and_(mask, col_mask)

        if mask is not None:
            table = table.filter(mask)

        return table.to_pandas()

    def get_headquarters_addresses(self, sirens: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get headquarters addresses for a list of SIRENs.

        Memory efficient: filters parquet file without loading entire dataset.

        Args:
            sirens: List of 9-digit SIREN numbers

        Returns:
            Dict mapping SIREN to address info:
            {
                "443061841": {
                    "street": "1 RUE EXAMPLE",
                    "postal_code": "75001",
                    "city": "PARIS",
                    "status": "active"
                }
            }
        """
        import pandas as pd
        import pyarrow as pa

        if not sirens:
            return {}

        sirens_list = [str(s) for s in sirens]

        df = self._query_parquet(
            [
                ("siren", "in", pa.array(sirens_list)),
                ("etablissementSiege", "==", True),
            ]
        )

        result = {}
        for _, row in df.iterrows():
            siren = row["siren"]

            num = str(row["numeroVoieEtablissement"] or "").strip()
            type_voie = str(row["typeVoieEtablissement"] or "").strip()
            voie = str(row["libelleVoieEtablissement"] or "").strip()
            street = f"{num} {type_voie} {voie}".strip()

            result[siren] = {
                "street": street if street else None,
                "postal_code": row["codePostalEtablissement"],
                "city": row["libelleCommuneEtablissement"],
                "status": "active"
                if row["etatAdministratifEtablissement"] == "A"
                else "closed",
            }

            if pd.notna(row["coordonneeLambertAbscisseEtablissement"]):
                result[siren]["lambert_x"] = float(
                    row["coordonneeLambertAbscisseEtablissement"]
                )
                result[siren]["lambert_y"] = float(
                    row["coordonneeLambertOrdonneeEtablissement"]
                )

        return result

    def get_all_establishments(self, siren: str) -> List[Dict[str, Any]]:
        """
        Get all establishments for a SIREN from stock file.

        Args:
            siren: 9-digit SIREN number

        Returns:
            List of establishment dicts with address info
        """
        import pandas as pd

        df = self._query_parquet([("siren", "==", str(siren))])

        results = []
        for _, row in df.iterrows():
            num = str(row["numeroVoieEtablissement"] or "").strip()
            type_voie = str(row["typeVoieEtablissement"] or "").strip()
            voie = str(row["libelleVoieEtablissement"] or "").strip()
            street = f"{num} {type_voie} {voie}".strip()

            etab = {
                "siret": row["siret"],
                "siren": row["siren"],
                "is_headquarters": bool(row["etablissementSiege"]),
                "street": street if street else None,
                "postal_code": row["codePostalEtablissement"],
                "city": row["libelleCommuneEtablissement"],
                "status": "active"
                if row["etatAdministratifEtablissement"] == "A"
                else "closed",
            }

            if pd.notna(row["coordonneeLambertAbscisseEtablissement"]):
                etab["lambert_x"] = float(row["coordonneeLambertAbscisseEtablissement"])
                etab["lambert_y"] = float(row["coordonneeLambertOrdonneeEtablissement"])

            results.append(etab)

        return results
