from __future__ import annotations

import sqlite3

from app.encyclopedia_db import init_encyclopedia_db
from app.encyclopedia_seed import seed_encyclopedia


def test_encyclopedia_schema_and_seed_are_idempotent(tmp_path):
    path = tmp_path / "encyclopedia.db"
    init_encyclopedia_db(path)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    first = seed_encyclopedia(conn)
    conn.commit()

    assert first == {"pests": 7, "diseases": 5, "treatments": 6, "sources": 8}
    assert conn.execute("SELECT COUNT(*) FROM pests").fetchone()[0] == 7
    assert conn.execute("SELECT COUNT(*) FROM diseases").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM treatments").fetchone()[0] == 6
    assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 8
    assert conn.execute("SELECT COUNT(*) FROM pest_treatments").fetchone()[0] > 0
    assert conn.execute("SELECT COUNT(*) FROM disease_treatments").fetchone()[0] > 0

    # Starter records are drafts awaiting review, never silently published.
    assert conn.execute(
        "SELECT COUNT(*) FROM pests WHERE review_status != 'needs_review'"
    ).fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM diseases WHERE review_status != 'needs_review'"
    ).fetchone()[0] == 0

    second = seed_encyclopedia(conn)
    conn.commit()
    assert second == {"pests": 0, "diseases": 0, "treatments": 0, "sources": 0}
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    conn.close()


def test_encyclopedia_database_does_not_create_personal_database(tmp_path):
    path = tmp_path / "reference" / "encyclopedia.db"
    init_encyclopedia_db(path)
    assert path.exists()
    assert not (tmp_path / "plants.db").exists()
