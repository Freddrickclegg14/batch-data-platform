import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.fannie_mae_columns import FILE_COLUMNS

ZIP_PATH = Path.home() / "Downloads"
OUT_DIR = Path("data/raw/fannie_mae")
CHUNK_SIZE = 500_000


def convert(zip_path: Path, csv_name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{zip_path.stem}.parquet"

    writer = None
    total_rows = 0

    with zipfile.ZipFile(zip_path, "r") as zf, zf.open(csv_name) as f:
        text_stream = io.TextIOWrapper(f, encoding="utf-8", newline="")

        df = pd.read_csv(
            text_stream,
            sep="|",
            header=None,
            names=FILE_COLUMNS,
            dtype=str,
            low_memory=False,
            chunksize=CHUNK_SIZE,
        )

        for i, chunk in enumerate(df, start=1):
            table = pa.Table.from_pandas(chunk, preserve_index=False)

            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema)

            writer.write_table(table)
            total_rows += len(chunk)
            print(
                f"  chunk {i}: wrote {len(chunk):,} rows (total so far: {total_rows:,})"
            )

    if writer is not None:
        writer.close()

    print(f"Done. Wrote {total_rows:,} rows to {out_path}")
    return out_path


def find_csv_in_zip(zip_path: Path, override: str | None = None) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
    if override:
        if override not in names:
            raise FileNotFoundError(
                f"{override} not in {zip_path.name}. contents: {names}"
            )
        return override
    csvs = [n for n in names if n.lower().endswith(".csv")]
    if not csvs:
        raise FileNotFoundError(f"No csv in {zip_path.name}. contents: {names}")
    if len(csvs) > 1:
        raise RuntimeError(
            f"Multiple csvs in {zip_path.name}: {csvs}.Pass --csv-name to disambiguate."
        )
    return csvs[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quarter",
        required=True,
        help="e.g. 2008Q1 or 2024Q1. format is <download-dir>/<quarter>.zip.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=ZIP_PATH,
        help=f"Where the quarterly zip lives (default: {ZIP_PATH})",
    )
    parser.add_argument(
        "--csv-name",
        default=None,
        help="CSV filename inside the zip.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help=f"Bronze output dir (default: {OUT_DIR})",
    )
    args = parser.parse_args()

    zip_path = args.download_dir / f"{args.quarter}.zip"
    if not zip_path.exists():
        raise SystemExit(
            f"Zip not found: {zip_path}. "
            f"Download {args.quarter} from Data Dynamics into {args.download_dir}"
        )

    csv_name = find_csv_in_zip(zip_path, args.csv_name)
    print(f"reading {csv_name} from {zip_path.name}")
    convert(zip_path, csv_name, args.out_dir)


if __name__ == "__main__":
    main()
