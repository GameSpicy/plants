# Taxonomy foundation — implementation notes

Updated: 2026-11-07

## Data model

The shared encyclopedia now records:
- `scientific_name`: the catalog's current display/lookup name for this taxon record.
- `accepted_name`: accepted botanical name when individually checked; otherwise the submitted name pending review.
- `rank`: currently `species` or `cultivar` for imported catalog records.
- `parent_name` and optional `parent_taxon_id`: cultivar parent as supplied/parsed, with a foreign-key relationship only when the exact parent species exists in the catalog.
- `cultivar_epithet`: parsed cultivar epithet, not a separate species epithet.
- `taxonomy_status`: `needs_review`, `verified`, `conflicting`, or `unresolved`.
- `taxonomy_source_url`: direct evidence URL for an individually reviewed name.
- `taxon_names`: common names and synonyms.
- `taxon_id_aliases`: legacy catalog IDs retained when exact submitted scientific-name duplicates are consolidated.

The schema update is additive and non-destructive. Existing encyclopedia databases gain missing columns; the personal `plants.db` is not opened or modified by this migration.

## Initial POWO-checked records (21)

The first two review batches have individually checked 21 catalog records against Kew Plants of the World Online (POWO). The accepted-name source is recorded per taxon in `TAXONOMY_OVERRIDES`.

| Catalog ID | Accepted name | Synonym retained | Source |
|---|---|---|---|
| plant-001 | Epipremnum aureum | — | https://powo.science.kew.org/taxon/87014-1 |
| plant-006 | Scindapsus pictus | — | https://powo.science.kew.org/taxon/88905-1 |
| plant-008 | Monstera deliciosa | — | https://powo.science.kew.org/taxon/87478-1 |
| plant-009 | Monstera adansonii | — | https://powo.science.kew.org/taxon/87464-1 |
| plant-010 | Rhaphidophora tetrasperma | — | https://powo.science.kew.org/taxon/88594-1 |
| plant-011 | Philodendron hederaceum | — | https://powo.science.kew.org/taxon/87797-1 |
| plant-016 | Philodendron xanadu | Thaumatophyllum xanadu | https://powo.science.kew.org/taxon/20011461-1 |
| plant-020 | Zamioculcas zamiifolia | — | https://powo.science.kew.org/taxon/89402-1 |
| plant-022 | Dracaena trifasciata | Sansevieria trifasciata | https://powo.science.kew.org/taxon/77164235-1 |
| plant-024 | Chlorophytum comosum | — | https://powo.science.kew.org/taxon/532810-1 |
| plant-025 | Ficus elastica | — | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:60458499-2 |
| plant-027 | Ficus lyrata | — | https://powo.science.kew.org/taxon/853158-1 |
| plant-028 | Ficus benjamina | — | https://powo.science.kew.org/taxon/852486-1 |
| plant-029 | Ficus microcarpa | — | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:853217-1 |
| plant-030 | Pachira aquatica | — | https://powo.science.kew.org/taxon/179762-2 |
| plant-031 | Heptapleurum arboricola | Schefflera arboricola | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:90845-1 |
| plant-032 | Codiaeum variegatum | — | https://powo.science.kew.org/taxon/85073-3 |
| plant-033 | Cordyline fruticosa | — | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:533580-1 |
| plant-034 | Dracaena reflexa | — | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:534338-1 |
| plant-035 | Dracaena fragrans | — | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:534207-1 |
| plant-036 | Dracaena sanderiana | — | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:60471006-2 |

The initial manually checked set contains 21 records. The subsequent WCVP v16 review is recorded in `app/data/taxonomy/wcvp_v16_catalog_review_163.csv` and imported by the taxonomy seeder. It adds 145 exact accepted-name matches, 12 cultivar-parent-only matches (retained as `needs_review` at cultivar rank), and 6 unresolved names. Combined with the initial set, 166 taxa have an exact accepted-name result; 12 cultivar identities remain pending and 6 names remain unresolved. A WCVP match verifies only the taxonomic name: it does not verify care, toxicity, pests, disease or horticultural content. The imported data records WCVP status, direct POWO taxon URL and review notes for each row.

## Duplicate ID preservation

The original source catalog contains nine pairs sharing an identical submitted scientific name. The normalized catalog keeps the first ID as canonical and records the other nine IDs in `taxon_id_aliases`. Their common names remain searchable through `taxon_names`. Profile lookup resolves a legacy ID to the canonical profile and returns the legacy ID list.

## Cultivars

Quoted cultivar epithets are now parsed into cultivar rank, parent-name text and cultivar epithet. The importer links a cultivar to a parent taxon only when an exact matching parent species record exists. It deliberately leaves the relationship empty where the parent cannot be established from the current catalog; genus-only labels such as `Philodendron 'Birkin'` are not guessed into a species parent.

## Review boundary

The WCVP v16 snapshot covers all 184 normalized catalog records when combined with the original 21 reviewed records. Six unresolved botanical or horticultural names and 12 cultivar identities remain open for follow-up. Cultivar/trade-name identification may require a horticultural registry or breeder evidence and is not inferred from a parent-species WCVP match.

## Validation

Automated tests were expanded to cover schema fields, 21 cited POWO records, cultivar parsing, parent linking, duplicate-ID redirects, source references and idempotent seeding. These tests have not yet been executed in a runtime in this work session.


The taxonomy importer validates every WCVP row against a current catalog ID and submitted name before applying it. Exact matches receive `verified`; cultivar-parent-only matches remain `needs_review`; unresolved rows remain `unresolved`. The full WCVP v16 source file is retained so the imported fields are reproducible.
