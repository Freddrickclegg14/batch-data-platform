import io
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.fannie_mae_columns import FILE_COLUMNS

ZIP_PATH = Path("C:/Users/User/Downloads/2008Q1.zip")
CSV_FILENAME_ZIP = "2008Q1.csv"
OUT_DIR = Path("data/raw/fannie_mae")
CHUNK_SIZE = 500_000


def convert(zip_path: Path, csv_name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{zip_path.stem}.parquet"

    writer = None
    total_rows = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open(csv_name) as f:
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


if __name__ == "__main__":
    convert(ZIP_PATH, CSV_FILENAME_ZIP, OUT_DIR)
