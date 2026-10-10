import sqlite3
from pathlib import Path


class Store:
    def __init__(self, workspace):
        self.workspace = Path(workspace)
        self.database_path = self.workspace / "state.db"

    def initialize(self):
        self.workspace.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.database_path) as database:
            database.execute(
                """
                CREATE TABLE IF NOT EXISTS scope (
                    target TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def connect(self):
        if not self.database_path.exists():
            raise ValueError(
                "Workspace not initialized. Run: scanner init"
            )

        return sqlite3.connect(self.database_path)

    def add_target(self, target):
        with self.connect() as database:
            database.execute(
                "INSERT OR IGNORE INTO scope (target) VALUES (?)",
                (target,),
            )

    def list_targets(self):
        with self.connect() as database:
            rows = database.execute(
                "SELECT target FROM scope ORDER BY target"
            ).fetchall()

        return [row[0] for row in rows]
