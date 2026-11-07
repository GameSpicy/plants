# Plant profile content — schema and review workflow

Updated: 2026-11-07

## Scope

Plant Profile v1 adds independently reviewable, sourced sections to each shared encyclopedia taxon. It does not alter personal plant records, photographs, observations, reminders, or treatment history. Those remain in the separate `plants.db`.

The existing catalog has 184 canonical entries. Profiles are populated and reviewed in small, ordered batches. A taxonomic name marked verified does not imply that its horticultural care, toxicity, or pest/disease information is verified.

## Section model

The `taxon_profile_sections` table stores one row per taxon and section:

- `section_key`: stable machine key such as `overview`, `identification`, `light`, `watering`, `soil`, `temperature`, `humidity`, `fertilizing`, `pruning`, `propagation`, `toxicity`, `seasonal_care`, or `common_problems`.
- `title` and `content`: display label and authored reference content.
- `confidence`: `unreviewed`, `low`, `medium`, or `high`.
- `review_status`: `draft`, `needs_review`, `verified`, or `retired`.
- `source_note`, `reviewed_at`, and `updated_at`: editorial provenance and review tracking.

Sources are normalized in `sources` and linked through `content_references` using `content_type='taxon_section'` and `content_id='<taxon_id>:<section_key>'`. This allows each section to have its own citations. A general source may be linked only for the limited context it supports; it must not be presented as evidence for an unsupported species-specific claim.

Existing structured fields remain available: taxonomy in `taxa`, baseline care in `care_profiles`, and feeding details in `fertilizer_guides`. The section model supplements these tables and does not replace them.

## Current import behavior

The catalog importer creates low-confidence, `needs_review` starter sections only when the catalog actually contains a value. The current starter sections are light, watering/drainage, soil, temperature, humidity, and toxicity. These are imported as review prompts, not completed botanical profiles.

The importer uses `INSERT OR IGNORE` for profile sections. This is deliberate: rerunning the catalog seed must not overwrite a human-reviewed section or locally curated content. A future explicit content-update workflow should update a section only when the incoming revision is authorized and reviewed.

The generic RHS houseplant source is attached to light, watering, and soil only as broad horticultural context. Toxicity notes from the starter catalog are not given a fabricated citation and remain unverified.

## First reviewed batch: plant-001 to plant-005

The first content batch covers the base pothos entry and four catalog cultivar entries: Golden, Marble Queen, Neon, and Manjula. Shared species-level care guidance is applied to these cultivar records, while cultivar identification is handled separately.

The batch contains sourced sections for overview, identification, light, watering, soil, temperature, humidity, fertilizing, pruning, propagation, toxicity, common problems, and seasonal care. Sources include Kew POWO, North Carolina State Extension, University of Wisconsin–Madison Extension, RHS, Clemson Extension, New York Botanical Garden, Singapore NParks, and UF/IFAS.

The Manjula-specific identification description remains `needs_review` because the sources reviewed for this batch did not establish a reliable cultivar-specific diagnostic description. This is intentional: the profile must show the gap rather than invent cultivar traits. The shared species-level guidance does not itself prove that every cultivar has identical growth characteristics.

The batch data is stored in `app/data/profile_batches/profile-001-005.json` and loaded repeat-safely by the catalog importer. Existing starter sections are upgraded only when the incoming batch is verified and the stored section is still draft or awaiting review. Existing verified sections are not silently overwritten.

## Second reviewed batch: plant-006 to plant-015

The second ordered batch covers Scindapsus pictus (including the catalog's 'Argyraeus' entry), Monstera deliciosa, Monstera adansonii, Rhaphidophora tetrasperma, Philodendron hederaceum (including 'Brasil'), Philodendron 'Birkin', Philodendron erubescens 'Pink Princess', and Philodendron gloriosum.

Care content is separated by species rather than reusing the pothos profile. In particular, Rhaphidophora tetrasperma is explicitly distinguished from Monstera; Monstera deliciosa propagation requires a node; and Scindapsus pictus is identified as a distinct Southeast Asian vine whose documented native range includes southeastern Bangladesh. The 'Brasil' identification uses the yellow central leaf band described by UConn Extension.

Cultivar uncertainty is retained. The catalog's Scindapsus pictus 'Argyraeus' record has a cultivar name listed by NC State but no independently verified unique diagnostic description in the sources reviewed, so its cultivar identification remains needs_review. Philodendron 'Birkin' remains needs_review at the taxonomy/content level because the RHS entry reports unresolved name status; the cultivar's pinstriped foliage description is recorded from NC State. Philodendron gloriosum care sections remain needs_review where only genus-level Philodendron guidance is available. Philodendron 'Pink Princess' has a distinct NParks profile and cultivar-level identification and care sources.

Batch data is stored in app/data/profile_batches/profile-006-015.json. Each section links only to the source used for that section, rather than attaching every source to every claim.

## Third reviewed batch: plant-016 to plant-025

The third ordered batch covers Philodendron xanadu, Aglaonema commutatum (two catalog display entries), Dieffenbachia seguine, Zamioculcas zamiifolia (including 'Raven'), Dracaena trifasciata (including 'Hahnii'), Chlorophytum comosum, and Ficus elastica.

The profiles use species-specific extension guidance. Examples of important differences include the dry-down preference of ZZ plants and snake plants, the more moisture-retentive but not saturated medium used for Aglaonema, Dieffenbachia's cane and vein-count identification features, and spider plant propagation by plantlets. Cultivar descriptions for Raven and Hahnii are separated from the parent species care notes.

Batch data is stored in app/data/profile_batches/profile-016-025.json. The Aglaonema and Chinese evergreen catalog entries share species-level care but retain separate display identities. No cultivar-specific care differences are claimed unless the cited source supports them.

## Fourth reviewed batch: plant-026 to plant-050

The fourth ordered batch adds 25 entries: Ficus elastica 'Burgundy', Ficus lyrata, Ficus benjamina, Ficus microcarpa, Pachira aquatica, Heptapleurum arboricola, Codiaeum variegatum, Cordyline fruticosa, Dracaena reflexa, Dracaena fragrans, Dracaena sanderiana, Caladium bicolor, Alocasia × amazonica (trade hybrid commonly sold as Polly), Alocasia zebrina, Alocasia macrorrhizos, Colocasia esculenta, Goeppertia orbifolia, Goeppertia insignis, Goeppertia ornata, Maranta leuconeura, Peperomia obtusifolia, Peperomia argyreia, Hypoestes phyllostachya, Coleus scutellarioides, and Tradescantia pallida.

The batch deliberately distinguishes plants with materially different moisture needs. ZZ-like dry-down advice is not reused for moisture-demanding Caladium or Colocasia; Alocasia is treated as an aroid with a warm, moist but aerated root zone; Goeppertia profiles distinguish consistently moist, high-humidity rainforest understory care; Peperomia obtusifolia and watermelon peperomia are kept on the drier, highly aerated side. Lucky bamboo is explicitly identified as Dracaena, not true bamboo.

Cultivar and hybrid uncertainty is retained. Ficus elastica 'Burgundy' and Alocasia × amazonica/Polly have species-level care notes but their cultivar/hybrid identification remains needs_review. Hypoestes and Maranta sections remain needs_review where the source mapping was not sufficiently confirmed in this review. These are not presented as complete verified profiles.

Sources are section-linked in app/data/profile_batches/profile-026-050.json. Primary references include NC State Extension, Clemson Extension, UF/IFAS, and Iowa State/University Extension material where relevant. Batch-specific source IDs were added to the importer. A section with no verified source is deliberately left without a citation and marked needs_review.

## Review sequence

Process canonical catalog IDs in ascending order, in batches of approximately 10–15 taxa. For each taxon:

1. Confirm the accepted taxon/cultivar identity and parent relationship.
2. Research each section using authoritative botanical gardens, university extension services, recognized horticultural institutions, and appropriate toxicology/veterinary references.
3. Write concise, actionable information. Separate species-specific evidence from genus/family-level context and inference.
4. Cite every section independently. Do not reuse a source for claims it does not support.
5. Mark unsupported sections as incomplete; do not fill them with generic guesses.
6. Set confidence and review status per section, not once for the whole plant.
7. Record review date and source metadata.
8. Run import, service, and foreign-key tests before proceeding to the next batch.

Suggested section coverage:

- Overview: native range, growth habit, mature size, growth rate, and notable characteristics.
- Identification: diagnostic leaf, stem, flower, fruit, and cultivar features where documented.
- Light: intensity, direct/filtered exposure, acclimation and scorch considerations.
- Watering: moisture preference, dry-down cues, seasonal adjustments and overwatering risks.
- Soil: texture, aeration, pH where evidence exists, and drainage.
- Temperature: preferred range and cold/heat sensitivity.
- Humidity: humidity tolerance and the importance of airflow.
- Fertilizing: suitable fertilizer category, active-growth guidance, reduced-feeding periods, deficiency/excess cautions. Do not invent NPK ratios or doses.
- Pruning: timing, tools, and plant-specific cautions.
- Propagation: supported methods and conditions.
- Toxicity: plant parts, known toxic principles/effects, affected animals or people, and source limitations.
- Seasonal care: locally relevant adjustments, clearly distinguished from general botanical requirements.
- Common problems: distinguish pests, pathogens, and abiotic stress; link to shared pest/disease records where supported.

## Review and release gates

A section is not `verified` merely because text exists. It needs an appropriate source, a clear claim-to-source relationship, and editorial review. Keep uncertainty visible. The full profile should be considered complete only when its applicable sections are populated and independently reviewed; not every section is relevant to every taxon.

Do not deploy profile content to the live Unraid database until the feature branch tests pass and the content batch has been reviewed. No migration in this document modifies `plants.db`.


## Fifth batch: plant-051 to plant-100

The fifth ordered batch adds 50 catalog entries, from Tradescantia zebrina through New Guinea impatiens. It covers foliage plants, ferns, palms and tropical flowering shrubs and bedding plants. The batch is stored in `app/data/profile_batches/profile-051-100.json`.

This batch is a practical, source-linked personal-use guide and is not a claim that all 50 profiles are fully verified. New species-level or clearly labeled genus-level guidance covers Syngonium podophyllum, several ferns, Pilea peperomioides, Aspidistra elatior, Strelitzia reginae, Ixora coccinea, Beaucarnea recurvata, tropical hibiscus, Gardenia jasminoides, Trachelospermum jasminoides, Pentas lanceolata, celosia, zinnia, cosmos, sunflower and Jatropha integerrima, alongside earlier coverage of Tradescantia, Fittonia, asparagus ferns, desert rose, periwinkle, oleander and lantana. ASPCA pet-toxicity listings are used only for the named palm taxa and only for the animal species covered. The ASPCA Boston fern record names *Nephrolepis exaltata bostoniensis*, so its cat/dog non-toxicity statement remains under review for the broader *N. exaltata* catalog entry.

High-priority safety sections now state the supported hazards for desert rose, Madagascar periwinkle, asparagus ferns, and oleander. Oleander is identified as highly poisonous in all parts, including dried material, and its pruning debris must not be burned. ASPCA pet listings now cover the named areca, parlor, majesty and ponytail palms; lady-palm evidence names Rhapis flabelliformis rather than the catalog species R. excelsa, so that profile stays provisional. These listings cover only their named animals and do not imply human safety. Lantana's source documents livestock toxicity and minor irritation from foliage and unripe berries; other exposure details remain under review.

Plant-094 remains *Jatropha integerrima* and now has matching UF/IFAS and Singapore NParks references for its identification, tropical care, propagation and ingestion/sap hazards. *Jatropha podagrica* evidence was not carried over to this entry. Genus-level sources are labeled as such, and uncertain cultivar, species and local-season details remain provisional drafts. Broad NC State annual-ornamental and container guides are not cited as evidence for individual taxa.


For personal use, the 051–100 batch now distinguishes `verified` source-backed sections from `draft` practical guidance. Draft is useful working advice and is not a botanical verification claim; identity or toxicity cautions remain provisional until a matching source is available. The batch contains 650 sections: 426 verified and 224 draft. All 93 previously terse or source-less requested sections were expanded in one pass: seasonal routines for Dhaka, conservative fertilizer guidance, two Fittonia problem notes, an areca temperature note, and toxicity wording for each entry. Bangladesh Meteorological Department climate context is cited only for season timing and rainfall patterns; RHS feeding guidance is cited only for general horticultural feeding principles, not species-specific doses. New ASPCA records cover staghorn fern, cast-iron plant, star jasmine, and a pet-safety overview listing Nephrolepis exaltata, Zinnia elegans and Helianthus. Toxicity claims are limited to the named animal groups and taxa; unassessed entries remain precautionary drafts, and seasonal/fertilizer advice remains practical rather than species-verified.
