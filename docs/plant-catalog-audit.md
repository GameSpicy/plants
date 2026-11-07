# Plant catalog audit — 2026-11-07

## Scope and method

Reviewed `app/catalog.py`, its `_merge_species_aliases()` normalization, and the current encyclopedia import path in `app/encyclopedia_catalog_seed.py` and `app/encyclopedia_db.py`. This is a structural and data-quality audit of the starter catalog, not a completed species-by-species taxonomic or horticultural verification. No existing catalog entries, personal plant records, or database files were changed by this audit.

## Inventory

- 193 raw catalog entries, with unique IDs in the source list.
- 184 normalized entries after exact scientific-name deduplication.
- 9 repeated scientific-name groups, each containing two common-name entries.
- Six broad categories: foliage, flowering, succulent & cactus, herb, tree & shrub, and climber & vine.
- 11 entries use quoted cultivar-style names in the scientific-name field.

The nine duplicate scientific-name groups are:

| Scientific name | Retained entry | Duplicate common-name entry |
|---|---|---|
| Aglaonema commutatum | plant-017 — Aglaonema | plant-018 — Chinese evergreen |
| Syngonium podophyllum | plant-053 — Syngonium | plant-054 — Arrowhead vine |
| Fittonia albivenis | plant-062 — Fittonia | plant-063 — Nerve plant |
| Pilea peperomioides | plant-064 — Pilea peperomioides | plant-065 — Chinese money plant |
| Hibiscus rosa-sinensis | plant-073 — Hibiscus | plant-074 — Chinese hibiscus |
| Tabernaemontana divaricata | plant-090 — Crape jasmine | plant-091 — Chandni |
| Plumeria rubra | plant-112 — Plumeria | plant-113 — Frangipani |
| Cestrum nocturnum | plant-114 — Night-blooming jasmine | plant-115 — Raat ki rani |
| Murraya paniculata | plant-164 — Murraya orange jasmine | plant-165 — Kamini |

The current normalizer retains the first record's ID and appends later common names as aliases. This avoids duplicate profiles, but the discarded IDs should be retained as legacy aliases or redirects if any existing personal records or external links refer to them.

## Findings

### 1. Care data is category-template guidance, not species-level care

Within each category, the same light, soil, humidity, temperature, toxicity, care and Bangladesh guidance is reused across many plants. For example, the 72 foliage entries share the same broad care text, and the flowering and succulent groups have similarly repeated templates.

These statements may be useful as cautious starter hints, but they are not sufficiently specific to publish as verified species guidance. Plants within a category can have very different light, watering, soil, heat, humidity and toxicity requirements. The current data should remain marked for review until each profile is checked against appropriate sources.

### 2. Taxonomy and cultivar representation need a stronger model

The importer treats any scientific-name string containing a single quote as rank `cultivar`, but the schema has no parent-taxon relationship. Cultivar names are therefore stored in `taxa.scientific_name` as if they were standalone scientific taxa. This makes it difficult to connect cultivar profiles to their accepted species, inherit appropriate species-level information, and distinguish formal cultivar names from trade names or marketing labels.

Recommendation: represent accepted botanical taxa separately from horticultural cultivars/selections. Add an explicit parent taxon or accepted-name relationship, store cultivar epithets separately, and keep common/trade names in `taxon_names`. Do not bulk-convert the existing quoted names without reviewing each one.

### 3. At least one scientific-name mapping needs correction

- `plant-016` is labelled “Philodendron xanadu” but currently stores `Thaumatophyllum xanadu`. Kew Plants of the World Online currently accepts `Philodendron xanadu` and lists `Thaumatophyllum xanadu` as a synonym. This should be corrected in a controlled taxonomy update, preserving the alternate name as a synonym. See [POWO: Philodendron xanadu](https://powo.science.kew.org/taxon/20011461-1).
- The catalog uses `Dracaena trifasciata` for snake plant. This agrees with POWO's accepted name; `Sansevieria trifasciata` is listed as a synonym. Keep the older name searchable as a synonym/common horticultural label. See [POWO: Dracaena trifasciata](https://powo.science.kew.org/taxon/77164235-1).

These are examples confirmed during the audit, not an exhaustive taxonomic review of all 184 normalized records.

### 4. Toxicity statements are too broad for safety-critical use

Many entries use genus/category-level phrases such as “species-dependent” or “many aroids are irritating or toxic if chewed.” These are useful warnings but do not answer whether a specific plant is toxic, which part is hazardous, or what exposure risk applies to pets and people. Do not present these generic fields as a definitive safety rating. Verify toxicity per accepted taxon and cite a suitable veterinary, poison-control, botanical or extension source.

### 5. Water intervals must not be interpreted as schedules

The catalog includes numeric `water_days` values. The code comment correctly says they are prompts rather than fixed schedules, but a numeric field can still be misread by users or downstream features. Prefer a soil-moisture trigger and conditions-based guidance; retain any interval only as a clearly labelled rough inspection reminder, never as an automatic watering instruction.

### 6. Bangladesh notes are useful context but need species-level review

The Dhaka/Bangladesh notes appropriately mention intense sun, monsoon rain, airflow and drainage. However, most are repeated by category. These should become localized overlays on top of verified plant-specific care, not substitutes for it. In particular, recommendations must distinguish balcony exposure, pot size, substrate, actual drainage and seasonal weather.

### 7. Catalog identity and personal-record compatibility need protection

The source list has stable IDs, but exact-name deduplication removes later IDs from the normalized search result. Before changing IDs, accepted names or merge behavior, check how personal plant records and UI links refer to catalog IDs. Preserve old IDs through an alias/redirect map; do not rewrite personal records as part of encyclopedia cleanup.

## Recommended remediation order

1. Add a taxonomy review ledger with one row per raw entry: raw ID, display name, submitted scientific name, accepted name, rank, parent taxon, synonyms, authority/source URL, review status and reviewer date.
2. Resolve the nine duplicate groups while preserving all nine secondary IDs as legacy aliases.
3. Correct confirmed accepted-name/synonym mappings, beginning with `plant-016`; verify every remaining name against POWO or World Flora Online before changing it.
4. Model cultivars as children/selections of accepted taxa rather than independent scientific species.
5. Replace generic category templates with sourced species-level care in small reviewed batches. Keep unverified fields visibly marked as provisional.
6. Verify toxicity separately for each plant.
7. Replace calendar-style watering values with soil- and condition-based prompts.
8. Add automated tests for duplicate accepted taxa, alias preservation, parent-taxon validity, unresolved names and personal-record ID compatibility.

## Audit decision

**The catalog is suitable as a provisional discovery list, not yet as a verified plant encyclopedia.** Keep all imported taxa at `needs_review`. Do not label the 184 normalized records as verified, and do not publish the category-template care or toxicity statements as definitive species advice.

No production deployment or personal database migration was performed.
