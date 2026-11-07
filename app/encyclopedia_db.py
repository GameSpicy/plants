"""Shared plant encyclopedia database.

This database is deliberately separate from the user's personal plants.db.
It stores reusable reference content only; personal observations, photos,
care events and treatment history remain in plants.db.

The initializer is idempotent and never deletes or rewrites existing data.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(os.getenv("PLANTS_DATA_DIR", "/app/data"))
ENCYCLOPEDIA_DB_PATH = Path(
    os.getenv("PLANTS_ENCYCLOPEDIA_DB", str(DATA_DIR / "encyclopedia.db"))
)

SCHEMA_VERSION = 2

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS encyclopedia_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS taxa (
    id TEXT PRIMARY KEY,
    scientific_name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    family TEXT,
    genus TEXT,
    rank TEXT NOT NULL DEFAULT 'species',
    accepted_name TEXT NOT NULL DEFAULT '',
    parent_name TEXT NOT NULL DEFAULT '',
    parent_taxon_id TEXT REFERENCES taxa(id) ON DELETE SET NULL,
    cultivar_epithet TEXT NOT NULL DEFAULT '',
    taxonomy_status TEXT NOT NULL DEFAULT 'needs_review'
        CHECK (taxonomy_status IN ('needs_review','verified','conflicting','unresolved')),
    taxonomy_source_url TEXT NOT NULL DEFAULT '',
    category TEXT,
    description TEXT NOT NULL DEFAULT '',
    growth_habit TEXT NOT NULL DEFAULT '',
    native_range TEXT NOT NULL DEFAULT '',
    mature_size TEXT NOT NULL DEFAULT '',
    growth_rate TEXT NOT NULL DEFAULT '',
    toxicity TEXT NOT NULL DEFAULT '',
    verification_status TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (verification_status IN ('unreviewed','needs_review','verified','deprecated')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_taxa_family ON taxa(family);
CREATE INDEX IF NOT EXISTS idx_taxa_genus ON taxa(genus);
CREATE INDEX IF NOT EXISTS idx_taxa_category ON taxa(category);

CREATE TABLE IF NOT EXISTS taxon_names (
    id INTEGER PRIMARY KEY,
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    name TEXT NOT NULL COLLATE NOCASE,
    language TEXT NOT NULL DEFAULT 'en',
    name_type TEXT NOT NULL DEFAULT 'common'
        CHECK (name_type IN ('common','synonym','cultivar','local','transliteration')),
    preferred INTEGER NOT NULL DEFAULT 0 CHECK (preferred IN (0,1)),
    UNIQUE(taxon_id, name, language, name_type)
);
CREATE INDEX IF NOT EXISTS idx_taxon_names_name ON taxon_names(name);

-- Old catalog IDs remain resolvable after duplicate-name consolidation.
CREATE TABLE IF NOT EXISTS taxon_id_aliases (
    legacy_id TEXT PRIMARY KEY,
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    reason TEXT NOT NULL DEFAULT 'duplicate_catalog_entry'
);

CREATE TABLE IF NOT EXISTS care_profiles (
    id INTEGER PRIMARY KEY,
    taxon_id TEXT NOT NULL UNIQUE REFERENCES taxa(id) ON DELETE CASCADE,
    light TEXT NOT NULL DEFAULT '',
    temperature_min_c REAL,
    temperature_max_c REAL,
    humidity_min_pct INTEGER,
    humidity_max_pct INTEGER,
    soil TEXT NOT NULL DEFAULT '',
    soil_ph_min REAL,
    soil_ph_max REAL,
    drainage TEXT NOT NULL DEFAULT '',
    watering TEXT NOT NULL DEFAULT '',
    pruning TEXT NOT NULL DEFAULT '',
    propagation TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (confidence IN ('unreviewed','low','medium','high')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fertilizer_guides (
    id TEXT PRIMARY KEY,
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    fertilizer_type TEXT NOT NULL DEFAULT '',
    npk_guidance TEXT NOT NULL DEFAULT '',
    active_growth_guidance TEXT NOT NULL DEFAULT '',
    dormant_season_guidance TEXT NOT NULL DEFAULT '',
    deficiency_signs TEXT NOT NULL DEFAULT '',
    excess_signs TEXT NOT NULL DEFAULT '',
    application_notes TEXT NOT NULL DEFAULT '',
    confidence TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (confidence IN ('unreviewed','low','medium','high')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seasonal_guides (
    id TEXT PRIMARY KEY,
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    season_key TEXT NOT NULL,
    guidance TEXT NOT NULL,
    UNIQUE(taxon_id, season_key)
);

CREATE TABLE IF NOT EXISTS pests (
    id TEXT PRIMARY KEY,
    common_name TEXT NOT NULL,
    scientific_name TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    appearance TEXT NOT NULL DEFAULT '',
    symptoms TEXT NOT NULL DEFAULT '',
    distinguishing_signs TEXT NOT NULL DEFAULT '',
    life_cycle TEXT NOT NULL DEFAULT '',
    prevention TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'moderate'
        CHECK (severity IN ('low','moderate','high','critical')),
    diagnostic_confidence TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (diagnostic_confidence IN ('unreviewed','low','medium','high')),
    review_status TEXT NOT NULL DEFAULT 'draft'
        CHECK (review_status IN ('draft','needs_review','verified','retired')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diseases (
    id TEXT PRIMARY KEY,
    common_name TEXT NOT NULL,
    causal_agent TEXT NOT NULL DEFAULT '',
    cause_type TEXT NOT NULL DEFAULT 'unknown'
        CHECK (cause_type IN ('fungal','oomycete','bacterial','viral','physiological','unknown')),
    description TEXT NOT NULL DEFAULT '',
    symptoms TEXT NOT NULL DEFAULT '',
    distinguishing_signs TEXT NOT NULL DEFAULT '',
    conditions_favouring TEXT NOT NULL DEFAULT '',
    prevention TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'moderate'
        CHECK (severity IN ('low','moderate','high','critical')),
    diagnostic_confidence TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (diagnostic_confidence IN ('unreviewed','low','medium','high')),
    review_status TEXT NOT NULL DEFAULT 'draft'
        CHECK (review_status IN ('draft','needs_review','verified','retired')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS treatments (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    treatment_type TEXT NOT NULL
        CHECK (treatment_type IN ('cultural','mechanical','biological','chemical','supportive','diagnostic')),
    purpose TEXT NOT NULL DEFAULT '',
    instructions TEXT NOT NULL DEFAULT '',
    active_ingredient_or_category TEXT NOT NULL DEFAULT '',
    safety_precautions TEXT NOT NULL DEFAULT '',
    follow_up TEXT NOT NULL DEFAULT '',
    label_and_regulation_note TEXT NOT NULL DEFAULT
        'Use only products legally approved for the intended plant and problem; follow the product label.',
    confidence TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (confidence IN ('unreviewed','low','medium','high')),
    review_status TEXT NOT NULL DEFAULT 'draft'
        CHECK (review_status IN ('draft','needs_review','verified','retired')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS taxon_pests (
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    pest_id TEXT NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL DEFAULT 'reported_host',
    notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (taxon_id, pest_id)
);

CREATE TABLE IF NOT EXISTS taxon_diseases (
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    disease_id TEXT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL DEFAULT 'reported_host',
    notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (taxon_id, disease_id)
);

CREATE TABLE IF NOT EXISTS pest_treatments (
    pest_id TEXT NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
    treatment_id TEXT NOT NULL REFERENCES treatments(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (pest_id, treatment_id)
);

CREATE TABLE IF NOT EXISTS disease_treatments (
    disease_id TEXT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    treatment_id TEXT NOT NULL REFERENCES treatments(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (disease_id, treatment_id)
);

CREATE TABLE IF NOT EXISTS media (
    id TEXT PRIMARY KEY,
    media_type TEXT NOT NULL DEFAULT 'image',
    url TEXT NOT NULL,
    thumbnail_url TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    attribution TEXT NOT NULL DEFAULT '',
    creator TEXT NOT NULL DEFAULT '',
    license TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    rights_status TEXT NOT NULL DEFAULT 'unverified'
        CHECK (rights_status IN ('unverified','approved','restricted','rejected')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS taxon_media (
    taxon_id TEXT NOT NULL REFERENCES taxa(id) ON DELETE CASCADE,
    media_id TEXT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0,1)),
    PRIMARY KEY (taxon_id, media_id)
);

CREATE TABLE IF NOT EXISTS pest_media (
    pest_id TEXT NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
    media_id TEXT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (pest_id, media_id)
);

CREATE TABLE IF NOT EXISTS disease_media (
    disease_id TEXT NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    media_id TEXT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (disease_id, media_id)
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    publisher TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    publication_date TEXT,
    accessed_at TEXT,
    source_type TEXT NOT NULL DEFAULT 'web',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS content_references (
    content_type TEXT NOT NULL,
    content_id TEXT NOT NULL,
    reference_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    claim TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (content_type, content_id, reference_id, claim)
);

CREATE TABLE IF NOT EXISTS content_revisions (
    id INTEGER PRIMARY KEY,
    content_type TEXT NOT NULL,
    content_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    change_summary TEXT NOT NULL DEFAULT '',
    review_status TEXT NOT NULL DEFAULT 'draft',
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(content_type, content_id, revision)
);

CREATE INDEX IF NOT EXISTS idx_taxon_pests_pest ON taxon_pests(pest_id);
CREATE INDEX IF NOT EXISTS idx_taxon_diseases_disease ON taxon_diseases(disease_id);
CREATE INDEX IF NOT EXISTS idx_content_references_content
    ON content_references(content_type, content_id);
"""

def init_encyclopedia_db(path: Path | str | None = None) -> None:
    """Create or upgrade the reference database without touching plants.db."""
    target = Path(path) if path else ENCYCLOPEDIA_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        # CREATE TABLE IF NOT EXISTS does not add columns to an existing database.
        # Apply additive, non-destructive migrations for installations on schema v1.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(taxa)")}
        additions = {
            "accepted_name": "TEXT NOT NULL DEFAULT ''",
            "parent_name": "TEXT NOT NULL DEFAULT ''",
            "parent_taxon_id": "TEXT REFERENCES taxa(id) ON DELETE SET NULL",
            "cultivar_epithet": "TEXT NOT NULL DEFAULT ''",
            "taxonomy_status": "TEXT NOT NULL DEFAULT 'needs_review'",
            "taxonomy_source_url": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE taxa ADD COLUMN {name} {definition}")
        conn.execute(
            "INSERT INTO encyclopedia_meta(key, value) VALUES('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(SCHEMA_VERSION),),
        )
        conn.commit()
    finally:
        conn.close()
