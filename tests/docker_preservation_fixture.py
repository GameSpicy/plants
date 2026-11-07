"""Build an isolated appdata fixture inside the image used by the Docker smoke test."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from app import main


def rows(connection: sqlite3.Connection, table: str) -> list[dict[str, object]]:
    order = "key" if table == "settings" else "token_hash" if table == "sessions" else "id"
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order}")]


def make_fixture(schema: str) -> None:
    main.init_db()
    photo_dir = Path(main.PHOTOS_DIR)
    photo_dir.mkdir(parents=True, exist_ok=True)
    photos = {
        "a" * 32 + ".jpg": b"\xff\xd8\xffplants-preservation-plant-photo\x00\xff\xd9",
        "b" * 32 + ".png": b"\x89PNG\r\n\x1a\nplants-preservation-event-photo\x00",
    }
    for name, content in photos.items():
        (photo_dir / name).write_bytes(content)

    with main.db() as connection:
        # Replace the fresh-install sample with stable, existing household data.
        connection.execute("DELETE FROM events")
        connection.execute("DELETE FROM tasks")
        connection.execute("DELETE FROM plants")
        connection.execute("DELETE FROM rooms")
        connection.execute("DELETE FROM sessions")
        connection.execute("DELETE FROM users")
        connection.execute("DELETE FROM settings")
        connection.execute(
            "INSERT INTO users(id,username,password_hash,salt,is_admin,active,created_at) VALUES(?,?,?,?,?,?,?)",
            (41, "fixture-admin", "fixture-password-hash", "fixture-salt", 1, 1, "2025-01-02T03:04:05+00:00"),
        )
        connection.execute("INSERT INTO rooms(id,name,sort) VALUES(11,'Sunroom',2)")
        connection.execute(
            """INSERT INTO plants(
                id,name,species,room_id,acquired,pot_size,pot_material,light,notes,info,
                care_source,outdoor,photo,created_by,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (73, "Preserved Monstera", "Monstera deliciosa", 11, "2022-04-03", "12 inch", "terracotta",
             "bright indirect", "Check soil before watering", "Existing plant info", "Extension guide", 0,
             "a" * 32 + ".jpg", 41, "2024-02-03T10:00:00+00:00", "2025-06-01T11:00:00+00:00"),
        )
        connection.execute(
            """INSERT INTO tasks(id,plant_id,kind,label,interval_days,winter_interval_days,last_done,
                cycle_start,snoozed_until,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (89, 73, "water", "Deep water", 9, 14, "2025-05-25", "2025-05-25", "2025-06-10",
             "2024-02-03T10:05:00+00:00"),
        )
        connection.execute(
            """INSERT INTO events(id,plant_id,task_id,kind,action,date,note,photo,user_id,via,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (97, 73, 89, "water", "done", "2025-05-25", "Filtered water; soil was dry", "b" * 32 + ".png",
             41, "fixture", "2025-05-25T08:30:00+00:00"),
        )
        main.set_setting(connection, "app_name", "Balcony & Sunroom")
        main.set_setting(connection, "winter_months", "[11,12,1,2]")
        main.set_setting(connection, "winter_multiplier", "1.5")
        connection.execute(
            "INSERT INTO sessions(token_hash,user_id,expires_at,created_at,via_token) VALUES(?,?,?,?,0)",
            ("fixture-session-hash", 41, "2099-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00"),
        )

    if schema == "legacy":
        with main.db() as connection:
            # These are the actual additive migrations in init_db: info is added,
            # and pre-via_token sessions are invalidated for a required sign-in.
            connection.execute("ALTER TABLE plants DROP COLUMN info")
            connection.execute("ALTER TABLE sessions DROP COLUMN via_token")

    database = sqlite3.connect(main.DB_PATH)
    database.row_factory = sqlite3.Row
    try:
        expected_tables = {
            name: rows(database, name)
            for name in ("users", "rooms", "plants", "tasks", "events", "settings")
        }
        if schema == "legacy":
            expected_tables["plants"] = [dict(row, info="") for row in expected_tables["plants"]]
        expected = {
            "schema": schema,
            "tables": expected_tables,
            "sessions": [] if schema == "legacy" else rows(database, "sessions"),
            "photo_hashes": {name: hashlib.sha256(content).hexdigest() for name, content in photos.items()},
            "photo_references": {"plant": "a" * 32 + ".jpg", "event": "b" * 32 + ".png"},
        }
    finally:
        database.close()
    (Path(main.DATA_DIR) / ".preservation-expected.json").write_text(json.dumps(expected), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("schema", choices=("current", "legacy"))
    make_fixture(parser.parse_args().schema)
