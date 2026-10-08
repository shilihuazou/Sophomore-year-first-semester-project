"""Copy the current SQLite demo database without sessions or test task records.

The source database is never modified. The output is for an offline competition
demonstration and preserves the existing administrator and six team records.
"""

from pathlib import Path
import os
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_ROOT / "app" / "backend" / "db.sqlite3"
OUTPUT = (
    PROJECT_ROOT
    / "参赛作品提交材料_20260929"
    / "04_相关数据"
    / "应用演示数据库"
    / "db.sqlite3"
)


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".sqlite3.tmp")
    if temporary.exists():
        raise FileExistsError(temporary)

    source = sqlite3.connect(f"file:{SOURCE.as_posix()}?mode=ro", uri=True)
    destination = sqlite3.connect(temporary)
    try:
        source.backup(destination)
        with destination:
            destination.execute("DELETE FROM django_session")
            destination.execute("DELETE FROM core_markerreport")
            destination.execute("DELETE FROM core_mapmarker")
            destination.execute("DELETE FROM django_admin_log WHERE user_id NOT IN (SELECT id FROM auth_user WHERE username = 'admin')")
            destination.execute("DELETE FROM auth_user_groups WHERE user_id NOT IN (SELECT id FROM auth_user WHERE username = 'admin')")
            destination.execute("DELETE FROM auth_user_user_permissions WHERE user_id NOT IN (SELECT id FROM auth_user WHERE username = 'admin')")
            destination.execute("DELETE FROM auth_user WHERE username <> 'admin'")
        counts = {
            table: destination.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "auth_user",
                "core_rescueteam",
                "core_mapmarker",
                "core_markerreport",
                "django_session",
            )
        }
        if counts != {
            "auth_user": 1,
            "core_rescueteam": 6,
            "core_mapmarker": 0,
            "core_markerreport": 0,
            "django_session": 0,
        }:
            raise RuntimeError(f"Unexpected clean database counts: {counts}")
    finally:
        destination.close()
        source.close()

    os.replace(temporary, OUTPUT)
    print(f"Prepared offline demo database: {OUTPUT}")


if __name__ == "__main__":
    main()
