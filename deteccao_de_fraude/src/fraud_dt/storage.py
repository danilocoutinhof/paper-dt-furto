from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def persist_dataframe(df: pd.DataFrame, table_name: str, database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
