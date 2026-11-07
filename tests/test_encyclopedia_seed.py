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


def test_botanical_catalog_imports_normalized_profiles_and_reference_links(tmp_path):
    from app.catalog import PLANT_CATALOG
    from app.encyclopedia_catalog_seed import seed_botanical_catalog
    from app.encyclopedia_service import get_taxon, search_taxa

    path = tmp_path / "encyclopedia.db"
    init_encyclopedia_db(path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    seed_encyclopedia(conn)
    imported = seed_botanical_catalog(conn)
    conn.commit()

    assert imported["taxa"] == len(PLANT_CATALOG)
    assert conn.execute("SELECT COUNT(*) FROM care_profiles").fetchone()[0] == len(PLANT_CATALOG)
    assert conn.execute("SELECT COUNT(*) FROM fertilizer_guides").fetchone()[0] == len(PLANT_CATALOG)
    assert conn.execute("SELECT COUNT(*) FROM taxon_pests").fetchone()[0] >= 8
    assert conn.execute("SELECT COUNT(*) FROM taxon_diseases").fetchone()[0] >= 2
    assert conn.execute("SELECT COUNT(*) FROM media WHERE rights_status='approved'").fetchone()[0] == 3
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert conn.execute("SELECT COUNT(*) FROM taxa WHERE verification_status!='needs_review'").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM taxa WHERE taxonomy_status='verified'").fetchone()[0] == 21
    assert conn.execute("SELECT COUNT(*) FROM taxon_id_aliases").fetchone()[0] == 9
    assert conn.execute("SELECT COUNT(*) FROM taxon_names WHERE name_type='synonym'").fetchone()[0] >= 3
    xanadu = conn.execute("SELECT scientific_name, accepted_name, taxonomy_status FROM taxa WHERE id='plant-016'").fetchone()
    assert tuple(xanadu) == ('Philodendron xanadu', 'Philodendron xanadu', 'verified')
    assert any(n["name"] == "Thaumatophyllum xanadu" for n in get_taxon("plant-016", path=path)["names"])
    golden = conn.execute("SELECT rank,parent_name,cultivar_epithet FROM taxa WHERE id='plant-002'").fetchone()
    assert tuple(golden) == ("cultivar", "Epipremnum aureum", "Golden")
    assert conn.execute("SELECT parent_taxon_id FROM taxa WHERE id='plant-002'").fetchone()[0] == "plant-001"
    assert conn.execute("SELECT parent_taxon_id FROM taxa WHERE id='plant-013'").fetchone()[0] is None
    assert conn.execute("SELECT COUNT(*) FROM content_references WHERE content_type='taxon' AND reference_id='source-powo'").fetchone()[0] == 21

    hibiscus = get_taxon("plant-073", path=path)
    assert hibiscus is not None
    legacy_hibiscus = get_taxon("plant-074", path=path)
    assert legacy_hibiscus is not None
    assert legacy_hibiscus["id"] == "plant-073"
    assert "plant-074" in legacy_hibiscus["legacy_ids"]
    assert any(p["id"] == "pest-aphids" for p in hibiscus["pests"])
    assert any("University of Minnesota" in source["publisher"] for source in hibiscus["sources"])

    pothos = get_taxon("plant-001", path=path)
    assert pothos is not None
    sections = {item["section_key"]: item for item in pothos["profile_sections"]}
    assert {"light", "watering", "soil", "temperature", "humidity", "toxicity"} <= set(sections)
    assert all(item["review_status"] == "needs_review" for item in sections.values())
    assert all(item["confidence"] == "low" for item in sections.values())
    assert any(source["id"] == "source-rhs-houseplants" for source in sections["light"]["sources"])
    assert sections["toxicity"]["sources"] == []
    assert len(pothos["media"]) == 3
    assert pothos["media"][0]["license"] == "CC BY-SA 4.0"
    assert pothos["fertilizer_guides"]
    assert pothos["fertilizer_guides"][0]["sources"]

    assert any(item["id"] == "plant-160" for item in search_taxa("Capsicum", path=path))

    # Regression: an existing installation may already contain a catalog row
    # with stale taxonomy. Re-seeding must refresh taxonomy fields, while
    # leaving independently enriched profile/content fields untouched.
    conn.execute(
        "UPDATE taxa SET accepted_name=?, taxonomy_status=?, taxonomy_source_url=?, "
        "description=? WHERE id='plant-016'",
        ("Thaumatophyllum xanadu", "needs_review", "", "Locally enriched description"),
    )
    conn.execute(
        "UPDATE care_profiles SET notes=? WHERE taxon_id='plant-016'",
        ("Locally edited care notes",),
    )
    second = seed_botanical_catalog(conn)
    refreshed = conn.execute(
        "SELECT accepted_name, taxonomy_status, taxonomy_source_url, description "
        "FROM taxa WHERE id='plant-016'"
    ).fetchone()
    assert tuple(refreshed) == (
        "Philodendron xanadu",
        "verified",
        "https://powo.science.kew.org/taxon/20011461-1",
        "Locally enriched description",
    )
    assert conn.execute(
        "SELECT notes FROM care_profiles WHERE taxon_id='plant-016'"
    ).fetchone()[0] == "Locally edited care notes"
    assert all(value == 0 for value in second.values())
    conn.close()
