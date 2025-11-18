from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "SQL"
DB_PATH = SQL_DIR / "schema.db"
SCHEMA_SQL = SQL_DIR / "schema.sql"
DATA_SQL = SQL_DIR / "sample_data.sql"


def run_sql_file(conn, path: Path):
    with path.open("r", encoding="utf-8") as f:
        conn.executescript(f.read())


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    print(f"Using database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        run_sql_file(conn, SCHEMA_SQL)
        run_sql_file(conn, DATA_SQL)
        conn.commit()
        print("Database initialized successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
