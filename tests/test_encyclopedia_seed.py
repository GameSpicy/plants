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


def test_read_only_service_returns_profiles_treatments_and_sources(tmp_path):
    from app.encyclopedia_service import get_problem, get_treatment, list_problems, list_treatments

    path = tmp_path / "encyclopedia.db"
    init_encyclopedia_db(path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    seed_encyclopedia(conn)
    conn.commit()
    conn.close()

    pests = list_problems("pests", q="mealy", path=path)
    assert len(pests) == 1
    assert pests[0]["id"] == "pest-mealybug"

    mealybug = get_problem("pests", "pest-mealybug", path=path)
    assert mealybug is not None
    assert any(item["id"] == "treatment-isolate-inspect" for item in mealybug["treatments"])
    assert any(item["publisher"] for item in mealybug["sources"])

    disease = get_problem("diseases", "disease-root-rot-complex", path=path)
    assert disease is not None
    assert disease["cause_type"] == "unknown"
    assert disease["treatments"]

    treatments = list_treatments(q="soap", path=path)
    assert len(treatments) == 1
    guide = get_treatment("treatment-insecticidal-soap-oil", path=path)
    assert guide is not None
    assert guide["safety_precautions"]
    assert guide["sources"]


def test_service_hides_retired_records(tmp_path):
    from app.encyclopedia_service import get_problem, list_problems

    path = tmp_path / "encyclopedia.db"
    init_encyclopedia_db(path)
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO pests(id, common_name, review_status, updated_at) VALUES(?,?,?,?)",
                 ("retired-pest", "Old pest", "retired", "2026-01-01"))
    conn.commit()
    conn.close()

    assert list_problems("pests", path=path) == []
    assert get_problem("pests", "retired-pest", path=path) is None
