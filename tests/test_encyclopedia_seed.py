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
    assert all(sections[key]["review_status"] == "verified" for key in ("light", "watering", "soil", "temperature", "humidity", "toxicity"))
    assert sections["toxicity"]["confidence"] == "high"
    assert any(source["id"] == "source-rhs-houseplants" for source in sections["light"]["sources"])
    assert any(source["id"] == "source-nparks-epipremnum" for source in sections["toxicity"]["sources"])
    overview_sources = {source["id"] for source in sections["overview"]["sources"]}
    assert "source-kew-epipremnum" in overview_sources
    assert sections["overview"]["review_status"] == "verified"
    manjula = get_taxon("plant-005", path=path)
    manjula_identification = next(
        item for item in manjula["profile_sections"] if item["section_key"] == "identification"
    )
    assert manjula_identification["review_status"] == "needs_review"
    assert manjula_identification["sources"] == []
    for taxon_id in ("plant-001", "plant-002", "plant-003", "plant-004", "plant-005"):
        profile = get_taxon(taxon_id, path=path)
        assert len(profile["profile_sections"]) >= 13
    # Ordered second profile batch: species care is separated, and unsupported cultivar claims stay pending.
    scindapsus = get_taxon("plant-006", path=path)
    satin = get_taxon("plant-007", path=path)
    monstera = get_taxon("plant-008", path=path)
    adansonii = get_taxon("plant-009", path=path)
    rhaphidophora = get_taxon("plant-010", path=path)
    heartleaf = get_taxon("plant-011", path=path)
    brasil = get_taxon("plant-012", path=path)
    birkin = get_taxon("plant-013", path=path)
    pink_princess = get_taxon("plant-014", path=path)
    gloriosum = get_taxon("plant-015", path=path)
    for profile in (scindapsus, satin, monstera, adansonii, rhaphidophora, heartleaf, brasil, birkin, pink_princess, gloriosum):
        assert len(profile["profile_sections"]) >= 13
    def section(profile, key):
        return next(item for item in profile["profile_sections"] if item["section_key"] == key)
    assert "not Epipremnum" in section(scindapsus, "overview")["content"]
    assert section(satin, "identification")["review_status"] == "needs_review"
    assert "node" in section(monstera, "propagation")["content"]
    assert "marginal splits" in section(adansonii, "identification")["content"]
    assert "does not make it a Monstera" in section(rhaphidophora, "identification")["content"]
    assert section(brasil, "identification")["review_status"] == "verified"
    assert section(birkin, "overview")["review_status"] == "needs_review"
    assert section(gloriosum, "light")["review_status"] == "needs_review"
    assert section(pink_princess, "identification")["review_status"] == "verified"
    assert any(src["id"] == "source-nparks-pink-princess" for src in section(pink_princess, "identification")["sources"])

    xanadu_profile = get_taxon("plant-016", path=path)
    aglaonema = get_taxon("plant-017", path=path)
    chinese_evergreen = get_taxon("plant-018", path=path)
    dieffenbachia = get_taxon("plant-019", path=path)
    zz = get_taxon("plant-020", path=path)
    raven = get_taxon("plant-021", path=path)
    snake = get_taxon("plant-022", path=path)
    hahnii = get_taxon("plant-023", path=path)
    spider = get_taxon("plant-024", path=path)
    rubber = get_taxon("plant-025", path=path)
    for profile in (xanadu_profile, aglaonema, chinese_evergreen, dieffenbachia, zz, raven, snake, hahnii, spider, rubber):
        assert len(profile["profile_sections"]) >= 13
    def section(profile, key):
        return next(item for item in profile["profile_sections"] if item["section_key"] == key)
    assert "clumping" in section(xanadu_profile, "overview")["content"]
    assert "top 1–2 inches" in section(aglaonema, "watering")["content"]
    assert "lateral veins" in section(dieffenbachia, "identification")["content"]
    assert "dry well" in section(zz, "watering")["content"]
    assert "nearly black" in section(raven, "identification")["content"]
    assert "dry between waterings" in section(snake, "watering")["content"]
    assert "funnel-shaped rosette" in section(hahnii, "identification")["content"]
    assert "plantlets" in section(spider, "overview")["content"]
    assert "latex" in section(rubber, "toxicity")["content"]

    # Fourth ordered batch: plant-026 through plant-050.
    batch_026_050 = [get_taxon(f"plant-{i:03d}", path=path) for i in range(26, 51)]
    assert all(profile is not None and len(profile["profile_sections"]) >= 13 for profile in batch_026_050)
    def section(profile, key):
        return next(item for item in profile["profile_sections"] if item["section_key"] == key)
    assert section(batch_026_050[0], "identification")["review_status"] == "needs_review"  # Burgundy cultivar
    assert "fiddle" in section(batch_026_050[1], "identification")["content"].lower()
    assert "braided" in section(batch_026_050[4], "identification")["content"].lower()
    assert "filtered light" in section(batch_026_050[5], "light")["content"]
    assert "not a true bamboo" in section(batch_026_050[10], "overview")["content"]
    assert section(batch_026_050[12], "identification")["review_status"] == "needs_review"  # Alocasia Polly hybrid
    assert "tuber" in section(batch_026_050[11], "overview")["content"]
    assert "fluoride" in section(batch_026_050[16], "watering")["content"]
    assert section(batch_026_050[19], "identification")["sources"] == []
    assert section(batch_026_050[22], "identification")["review_status"] == "needs_review"
    assert any(src["id"] == "source-ncsu-heptapleurum" for src in section(batch_026_050[5], "overview")["sources"])

    # Fifth ordered batch: plant-051 through plant-100.
    batch_051_100 = [get_taxon(f"plant-{i:03d}", path=path) for i in range(51, 101)]
    assert all(profile is not None and len(profile["profile_sections"]) >= 13 for profile in batch_051_100)
    def section(profile, key):
        return next(item for item in profile["profile_sections"] if item["section_key"] == key)
    assert section(batch_051_100[0], "identification")["review_status"] == "verified"
    assert "silver" in section(batch_051_100[0], "identification")["content"]
    assert any(src["id"] == "source-ncsu-tradescantia-zebrina" for src in section(batch_051_100[0], "identification")["sources"])
    assert section(batch_051_100[1], "identification")["review_status"] == "draft"
    assert section(batch_051_100[11], "overview")["review_status"] == "verified"  # Fittonia
    assert section(batch_051_100[22], "overview")["review_status"] == "verified"  # Hibiscus
    assert section(batch_051_100[26], "overview")["review_status"] == "verified"  # Gardenia
    assert section(batch_051_100[27], "overview")["review_status"] == "draft"  # Jasminum sambac; genus evidence only
    assert section(batch_051_100[41], "overview")["review_status"] == "verified"  # Oleander
    assert section(batch_051_100[41], "toxicity")["review_status"] == "verified"
    assert section(batch_051_100[9], "watering")["review_status"] == "verified"  # Asparagus densiflorus
    assert section(batch_051_100[11], "watering")["review_status"] == "verified"  # Fittonia
    assert section(batch_051_100[29], "watering")["review_status"] == "verified"  # Adenium obesum
    assert section(batch_051_100[41], "toxicity")["review_status"] == "verified"  # Oleander
    assert "smoke" in section(batch_051_100[41], "toxicity")["content"]
    assert "vinca alkaloids" in section(batch_051_100[31], "toxicity")["content"]
    assert section(batch_051_100[43], "toxicity")["review_status"] == "verified"  # Jatropha integerrima species-level source
    assert any(src["id"] == "source-nparks-jatropha" for src in section(batch_051_100[43], "toxicity")["sources"])
    assert any(src["id"] == "source-aspca-areca-palm" for src in section(batch_051_100[17], "toxicity")["sources"])
    assert any(src["id"] == "source-aspca-parlor-palm" for src in section(batch_051_100[18], "toxicity")["sources"])
    assert any(src["id"] == "source-ncsu-asparagus-setaceus" for src in section(batch_051_100[10], "toxicity")["sources"])
    # Every batch citation resolves to a registered source; unsupported generic guides
    # are not attached as evidence for individual species.
    registered_source_ids = {row[0] for row in conn.execute("SELECT id FROM sources")}
    for profile in batch_051_100:
        assert len({item["section_key"] for item in profile["profile_sections"]}) == 13
        for item in profile["profile_sections"]:
            assert all(source["id"] in registered_source_ids for source in item["sources"])
    assert any(src["id"] == "source-ncsu-tradescantia-zebrina" for src in section(batch_051_100[0], "overview")["sources"])
    assert any(src["id"] == "source-aspca-staghorn-fern" for src in section(batch_051_100[8], "toxicity")["sources"])
    assert any(src["id"] == "source-aspca-cast-iron-plant" for src in section(batch_051_100[15], "toxicity")["sources"])
    assert any(src["id"] == "source-aspca-star-jasmine" for src in section(batch_051_100[28], "toxicity")["sources"])
    assert "No matching toxicology assessment" in section(batch_051_100[48], "toxicity")["content"]
    for profile in batch_051_100:
        for key in ("fertilizing", "toxicity", "seasonal_care", "temperature", "common_problems"):
            item = section(profile, key)
            assert item["content"].strip()
            assert item["review_status"] in ("verified", "draft", "needs_review")

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
