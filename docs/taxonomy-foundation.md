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

## Individually checked POWO records

The first review batch expanded the individually checked set to eleven records:

| Catalog ID | Accepted name | Synonym retained | Source |
|---|---|---|---|
| plant-001 | Epipremnum aureum | — | https://powo.science.kew.org/taxon/87014-1 |
| plant-006 | Scindapsus pictus | — | https://powo.science.kew.org/taxon/88905-1 |
| plant-008 | Monstera deliciosa | — | https://powo.science.kew.org/taxon/87478-1 |
| plant-009 | Monstera adansonii | — | https://powo.science.kew.org/taxon/87464-1 |
| plant-010 | Rhaphidophora tetrasperma | — | https://powo.science.kew.org/taxon/88594-1 |
| plant-011 | Philodendron hederaceum | — | https://powo.science.kew.org/taxon/87797-1 |
| plant-020 | Zamioculcas zamiifolia | — | https://powo.science.kew.org/taxon/89402-1 |
| plant-024 | Chlorophytum comosum | — | https://powo.science.kew.org/taxon/532810-1 |
| plant-016 | Philodendron xanadu | Thaumatophyllum xanadu | https://powo.science.kew.org/taxon/20011461-1 |
| plant-031 | Heptapleurum arboricola | Schefflera arboricola | https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:90845-1 |
| plant-022 | Dracaena trifasciata | Sansevieria trifasciata | https://powo.science.kew.org/taxon/77164235-1 |

The remaining 173 normalized taxa stay `needs_review` at this point; cultivar/trade-name entries were not upgraded merely because their parent species was checked. The broader plant profile remains `needs_review`; verifying a name does not verify care, toxicity, pests, disease or other horticultural content.

## Duplicate ID preservation

The original source catalog contains nine pairs sharing an identical submitted scientific name. The normalized catalog keeps the first ID as canonical and records the other nine IDs in `taxon_id_aliases`. Their common names remain searchable through `taxon_names`. Profile lookup resolves a legacy ID to the canonical profile and returns the legacy ID list.

## Cultivars

Quoted cultivar epithets are now parsed into cultivar rank, parent-name text and cultivar epithet. The importer links a cultivar to a parent taxon only when an exact matching parent species record exists. It deliberately leaves the relationship empty where the parent cannot be established from the current catalog; genus-only labels such as `Philodendron 'Birkin'` are not guessed into a species parent.

## Review boundary

This is a foundation and a small verified pilot, not a completed taxonomic audit of all catalog entries. All other names remain `needs_review`. The remaining catalog needs individual accepted-name and synonym checks against POWO/WCVP or another appropriate botanical backbone. Cultivar/trade-name identification may also require horticultural registry or breeder evidence and should not be inferred from a quoted string alone.

## Validation

Automated tests were expanded to cover schema fields, eleven cited POWO records, cultivar parsing, parent linking, duplicate-ID redirects, source references and idempotent seeding. These tests have not yet been executed in a runtime in this work session.
