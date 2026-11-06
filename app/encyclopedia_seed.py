"""Curated starter content for the shared plant-problem encyclopedia.

Entries are intentionally conservative and marked needs_review. They are
general diagnostic starting points, not a substitute for confirming the cause
on the individual plant. Sources are stored as records for in-app attribution.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

PESTS = [
    {
        "id": "pest-mealybug",
        "common_name": "Mealybugs",
        "scientific_name": "Pseudococcidae",
        "description": "Small sap-feeding insects with oval bodies and a white, waxy or cotton-like covering. They often gather in protected crevices.",
        "appearance": "White waxy filaments or cotton-like clusters; individual insects are soft-bodied and oval.",
        "symptoms": "Sticky honeydew, yellowing, stunted growth, leaf drop and sometimes black sooty mould growing on honeydew.",
        "distinguishing_signs": "Look at leaf axils, stem joints, undersides and roots. Cottony egg sacs and visible segmented insects support identification; white residue alone is not conclusive.",
        "life_cycle": "Eggs or live young are produced depending on species; mobile crawlers disperse before settling and developing a wax covering.",
        "prevention": "Inspect new plants and undersides of leaves; isolate new arrivals; avoid excessive nitrogen fertilization; inspect pots and supports.",
        "severity": "moderate",
    },
    {
        "id": "pest-spider-mites",
        "common_name": "Spider mites",
        "scientific_name": "Tetranychidae (including Tetranychus urticae)",
        "description": "Tiny plant-feeding mites, commonly found on leaf undersides. They are arachnids, not insects.",
        "appearance": "Very small moving dots; some species produce fine webbing when populations are high.",
        "symptoms": "Fine pale stippling, yellowing, bronzing, dry leaves and sometimes delicate webbing around leaf stalks or growing points.",
        "distinguishing_signs": "Use a hand lens and inspect leaf undersides. Tap foliage over white paper and look for tiny moving specks. Stippling alone can also have other causes.",
        "life_cycle": "Egg, larval, nymphal and adult stages; development can be rapid in warm, dry conditions.",
        "prevention": "Inspect plants regularly, reduce dust, avoid drought stress and check nearby plants when an infestation is found.",
        "severity": "moderate",
    },
    {
        "id": "pest-scale-insects",
        "common_name": "Scale insects",
        "scientific_name": "Coccoidea",
        "description": "Sap-feeding insects that often remain attached to stems or leaf surfaces beneath a waxy or shell-like covering.",
        "appearance": "Small fixed bumps that may be brown, tan, grey or white; soft scales may produce honeydew.",
        "symptoms": "Sticky leaves, sooty mould, yellowing, reduced vigour, leaf drop and dieback in heavier infestations.",
        "distinguishing_signs": "Check whether bumps can be gently lifted or scraped to reveal an insect body. Do not confuse natural plant features or lenticels with scale.",
        "life_cycle": "Many species have a mobile crawler stage; later stages become relatively immobile under protective coverings.",
        "prevention": "Inspect stems and leaf undersides on new plants; isolate affected plants; monitor for crawlers and ants associated with honeydew.",
        "severity": "moderate",
    },
    {
        "id": "pest-aphids",
        "common_name": "Aphids",
        "scientific_name": "Aphidoidea",
        "description": "Small, soft-bodied sap-feeding insects that cluster on tender shoots, buds and leaf undersides.",
        "appearance": "Often green, black, yellow or pink; pear-shaped bodies, long antennae and sometimes paired cornicles near the rear.",
        "symptoms": "Curled or distorted new growth, sticky honeydew, cast skins and sometimes sooty mould.",
        "distinguishing_signs": "Look for colonies on tender growth and shed white skins. Distortion without visible aphids may have other causes.",
        "life_cycle": "Many species reproduce rapidly by live birth during favourable conditions; winged forms can disperse to new plants.",
        "prevention": "Inspect new growth, avoid excessive nitrogen, remove heavily infested tips where appropriate and conserve natural predators.",
        "severity": "low",
    },
    {
        "id": "pest-thrips",
        "common_name": "Thrips",
        "scientific_name": "Thysanoptera",
        "description": "Very slender, small insects that rasp plant tissue and feed on cell contents, often hiding in flowers and folded new growth.",
        "appearance": "Narrow, elongated insects; adults may have narrow fringed wings. Immature stages are often pale and wingless.",
        "symptoms": "Silvery or bronze scarring, distorted new leaves or flowers, pale patches and tiny dark faecal spots.",
        "distinguishing_signs": "Tap flowers or leaves over white paper and inspect with magnification. Silvery damage and black specks together are suggestive but not definitive.",
        "life_cycle": "Eggs are inserted into plant tissue; immature stages feed on plants, with some later stages occurring in protected sites or growing media.",
        "prevention": "Inspect new plants and flowers, remove badly affected plant parts, keep the growing area clean and monitor with sticky cards as a detection aid.",
        "severity": "moderate",
    },
    {
        "id": "pest-whiteflies",
        "common_name": "Whiteflies",
        "scientific_name": "Aleyrodidae",
        "description": "Small sap-feeding insects whose adults fly up in a cloud when an infested plant is disturbed; immature stages remain attached to leaf undersides.",
        "appearance": "Tiny white, moth-like adults; flat pale scale-like immature stages on leaf undersides.",
        "symptoms": "Yellowing, reduced vigour, sticky honeydew and sooty mould in some infestations.",
        "distinguishing_signs": "Gently disturb foliage and inspect undersides for attached immature stages. Yellowing alone is not diagnostic.",
        "life_cycle": "Eggs and several immature stages occur on leaf undersides before winged adults emerge.",
        "prevention": "Inspect leaf undersides on new plants, isolate infested plants, remove heavily infested leaves when practical and monitor adults.",
        "severity": "moderate",
    },
    {
        "id": "pest-fungus-gnats",
        "common_name": "Fungus gnats",
        "scientific_name": "Sciaridae",
        "description": "Small dark flies associated with moist growing media. Larvae live in the substrate and feed mainly on fungi and decaying organic matter, but may injure fine roots.",
        "appearance": "Tiny dark, mosquito-like flies around pots; larvae are translucent to whitish with dark heads in the growing medium.",
        "symptoms": "Adult flies around pots; severe larval activity can contribute to poor root health or seedling damage. Adult presence alone does not prove root damage.",
        "distinguishing_signs": "Use yellow sticky cards to monitor adults and inspect the upper growing medium for larvae. Do not confuse them with fruit flies or shore flies.",
        "life_cycle": "Eggs and larvae develop in moist organic growing media; adults emerge and are attracted to damp pots.",
        "prevention": "Avoid persistently wet media, improve drainage, remove decaying debris and allow the surface layer to dry as appropriate for the plant.",
        "severity": "low",
    },
]

DISEASES = [
    {
        "id": "disease-root-rot-complex",
        "common_name": "Root rot (diagnostic syndrome)",
        "causal_agent": "Often associated with prolonged saturation and may involve oomycetes or fungi; not one single disease.",
        "cause_type": "unknown",
        "description": "A decline syndrome involving damaged roots. Waterlogged or poorly aerated media can injure roots directly and favour root pathogens.",
        "symptoms": "Persistent wilting despite wet media, yellowing, stalled growth and roots that are brown or black, soft and sometimes foul-smelling.",
        "distinguishing_signs": "Inspect roots and growing medium. Brown roots alone do not confirm a pathogen; distinguish dead roots from naturally darker healthy roots and consider drought, salts and cold injury.",
        "conditions_favouring": "Poor drainage, compacted media, oversized pots, blocked drainage holes and frequent watering that keeps the root zone saturated.",
        "prevention": "Use a suitable airy substrate and a pot with drainage; match watering to plant, pot and conditions; empty cachepots and saucers after watering.",
        "severity": "high",
    },
    {
        "id": "disease-powdery-mildew",
        "common_name": "Powdery mildew",
        "causal_agent": "Various powdery mildew fungi (order Erysiphales).",
        "cause_type": "fungal",
        "description": "A group of fungal diseases producing superficial powdery colonies on leaves, stems or flowers.",
        "symptoms": "White to grey powdery patches that may expand, with leaf distortion, yellowing or premature leaf drop in severe cases.",
        "distinguishing_signs": "Colonies appear on plant surfaces and may spread beyond dust-like deposits. Residue, mineral deposits and spray marks can look similar; confirm before treatment.",
        "conditions_favouring": "Susceptible hosts, moderate temperatures, high local humidity and limited air movement; free water is not required for many powdery mildew fungi.",
        "prevention": "Provide appropriate spacing and airflow, remove affected debris and avoid excessive nitrogen-driven soft growth.",
        "severity": "moderate",
    },
    {
        "id": "disease-botrytis-grey-mould",
        "common_name": "Grey mould",
        "causal_agent": "Botrytis cinerea and related Botrytis species.",
        "cause_type": "fungal",
        "description": "A fungal disease that commonly colonizes senescent, wounded or persistently damp plant tissue.",
        "symptoms": "Water-soaked or brown lesions followed by fuzzy grey sporulation, often on flowers, leaves or stems.",
        "distinguishing_signs": "Grey fuzzy growth on decaying tissue is suggestive. General brown patches without sporulation can result from sun, heat, injury or other pathogens.",
        "conditions_favouring": "Persistently damp plant surfaces, high humidity, poor airflow, crowded growth and dead plant material.",
        "prevention": "Remove dead flowers and leaves, improve airflow, avoid prolonged leaf wetness and water the growing medium rather than routinely wetting foliage.",
        "severity": "moderate",
    },
    {
        "id": "disease-bacterial-leaf-spot",
        "common_name": "Bacterial leaf spot (complex)",
        "causal_agent": "Various plant-pathogenic bacteria; the causal species depends on host and symptoms.",
        "cause_type": "bacterial",
        "description": "A symptom group caused by several bacterial pathogens. Visual symptoms overlap with fungal disease and abiotic leaf injury.",
        "symptoms": "Water-soaked or translucent lesions that may become brown or black; some lesions have yellow halos or follow leaf veins.",
        "distinguishing_signs": "Appearance alone rarely identifies the bacterium. Check whether spots expand, are water-soaked, and occur on multiple leaves; laboratory diagnosis may be needed.",
        "conditions_favouring": "Wet foliage, splashing water, contaminated tools, wounds and warm humid conditions for many bacterial leaf-spot pathogens.",
        "prevention": "Avoid splashing between plants, keep foliage dry where practical, sanitize tools, remove badly affected tissue and use clean propagation material.",
        "severity": "moderate",
    },
    {
        "id": "disease-viral-mosaic",
        "common_name": "Viral mosaic and leaf distortion (symptom group)",
        "causal_agent": "Various plant viruses; a specific virus cannot be identified from mosaic symptoms alone.",
        "cause_type": "viral",
        "description": "A group of viral disorders that may cause mosaic patterns, rings, distortion or abnormal growth. Nutrient imbalance and pests can mimic some symptoms.",
        "symptoms": "Irregular light and dark green or yellow patterns, distorted leaves, rings, stunting or abnormal flower colour depending on host and virus.",
        "distinguishing_signs": "Persistent patterned symptoms on successive new leaves raise suspicion, but visual inspection cannot reliably identify a virus. Confirm with a diagnostic laboratory where possible.",
        "conditions_favouring": "Infected propagation material and transmission by certain vectors or contaminated tools, depending on the virus.",
        "prevention": "Use healthy propagation stock, disinfect tools between plants, control known vectors and avoid propagating from symptomatic plants.",
        "severity": "high",
    },
]

TREATMENTS = [
    {
        "id": "treatment-isolate-inspect",
        "title": "Isolate and inspect an affected plant",
        "treatment_type": "cultural",
        "purpose": "Reduce the chance of spread while the cause is being identified.",
        "instructions": "Move the affected plant away from other plants when practical. Inspect both leaf surfaces, growing tips, stems, pot rim and growing medium. Use a hand lens where available. Avoid sharing tools or runoff water until the problem is understood.",
        "safety_precautions": "Wash hands after handling suspected pests or diseased tissue. Clean tools and work surfaces between plants.",
        "follow_up": "Reinspect the plant and nearby plants regularly; record whether new symptoms or pests appear.",
    },
    {
        "id": "treatment-water-wash",
        "title": "Wash exposed soft-bodied pests from foliage",
        "treatment_type": "mechanical",
        "purpose": "Physically reduce exposed aphids, mites, whiteflies and some other soft-bodied pests.",
        "instructions": "Where the plant tolerates it, rinse affected foliage with a controlled stream of water, paying attention to leaf undersides. Prevent contaminated runoff from reaching other pots. Repeat inspection because eggs and hidden individuals may remain.",
        "safety_precautions": "Avoid damaging delicate leaves, water-sensitive flowers or media that must remain dry. Do not leave the plant waterlogged.",
        "follow_up": "Check leaf undersides and new growth after washing; repeat only as needed and as the plant tolerates.",
    },
    {
        "id": "treatment-prune-dispose",
        "title": "Remove heavily infested or diseased plant parts",
        "treatment_type": "mechanical",
        "purpose": "Lower pest or disease pressure when affected tissue can be removed without unacceptable harm to the plant.",
        "instructions": "Prune only affected parts where appropriate. Place removed material directly into a bag and dispose of it; do not compost material when a spreading pest or pathogen is suspected. Clean tools between cuts and plants.",
        "safety_precautions": "Do not remove so much foliage that the plant is severely weakened. Wear gloves where sap or spines may irritate skin.",
        "follow_up": "Watch new growth and nearby plants for recurrence.",
    },
    {
        "id": "treatment-growing-media-correction",
        "title": "Correct persistently wet growing media",
        "treatment_type": "cultural",
        "purpose": "Reduce root-zone stress and conditions that favour fungus gnats and some root diseases.",
        "instructions": "Check drainage holes, remove standing water from outer pots or saucers, and assess whether the substrate is compacted or remains saturated. Adjust watering to the plant's needs and allow appropriate drying between waterings. Repot only when the medium or root condition warrants it.",
        "safety_precautions": "Do not impose a fixed dry-out schedule on plants that require consistently moist media. Avoid damaging healthy roots during inspection or repotting.",
        "follow_up": "Monitor substrate moisture, drainage and new growth; inspect roots again only if decline continues.",
    },
    {
        "id": "treatment-insecticidal-soap-oil",
        "title": "Consider labelled insecticidal soap or horticultural oil",
        "treatment_type": "chemical",
        "purpose": "Suppress susceptible exposed pests when non-chemical measures are insufficient.",
        "instructions": "Use only a product whose label explicitly permits the intended plant, pest and application setting. These contact materials require thorough coverage of the target pest; hidden insects and protected life stages may survive. Test a small area if the label permits and observe for plant injury.",
        "active_ingredient_or_category": "Insecticidal soap (potassium salts of fatty acids) or horticultural oil; product formulations differ.",
        "safety_precautions": "Follow the complete product label and local law. Observe PPE, ventilation, re-entry, pollinator and pet precautions. Avoid application during heat or plant water stress when the label or crop sensitivity indicates risk. Never mix products unless the label allows it.",
        "follow_up": "Reinspect at the interval specified by the product label. Do not assume one application eliminates eggs or hidden stages.",
    },
    {
        "id": "treatment-biological-control",
        "title": "Use an appropriate biological control",
        "treatment_type": "biological",
        "purpose": "Use natural enemies or microbial controls for a correctly identified target pest.",
        "instructions": "Select a biological control matched to the pest and growing environment, such as predatory mites for certain spider mites or an appropriately labelled microbial larvicide for fungus gnat larvae. Follow supplier instructions and avoid incompatible pesticide applications.",
        "active_ingredient_or_category": "Target-specific beneficial arthropods, entomopathogenic nematodes or Bacillus thuringiensis subsp. israelensis (Bti), where appropriate.",
        "safety_precautions": "Confirm target species and product identity. Follow supplier handling, storage and application directions; biological products are not interchangeable.",
        "follow_up": "Monitor pest numbers and biological-control establishment; allow for the time required by the organism or product.",
    },
]

SOURCES = [
    {
        "id": "source-ucipm-houseplant-problems",
        "title": "Houseplant Problems",
        "publisher": "University of California Statewide Integrated Pest Management Program",
        "url": "https://ipm.ucanr.edu/home-and-landscape/houseplant-problems/",
        "source_type": "extension",
    },
    {
        "id": "source-ucipm-mealybugs",
        "title": "Mealybugs",
        "publisher": "University of California Statewide Integrated Pest Management Program",
        "url": "https://ipm.ucanr.edu/home-and-landscape/mealybugs/",
        "source_type": "extension",
    },
    {
        "id": "source-ucipm-spider-mites",
        "title": "Spider Mites",
        "publisher": "University of California Statewide Integrated Pest Management Program",
        "url": "https://ipm.ucanr.edu/home-and-landscape/spider-mites/",
        "source_type": "extension",
    },
    {
        "id": "source-ucipm-scales",
        "title": "Scales",
        "publisher": "University of California Statewide Integrated Pest Management Program",
        "url": "https://ipm.ucanr.edu/home-and-landscape/scales/",
        "source_type": "extension",
    },
    {
        "id": "source-ucipm-fungus-gnats",
        "title": "Fungus Gnats",
        "publisher": "University of California Statewide Integrated Pest Management Program",
        "url": "https://ipm.ucanr.edu/home-and-landscape/fungus-gnats/",
        "source_type": "extension",
    },
    {
        "id": "source-ucipm-less-toxic",
        "title": "Less Toxic Insecticides",
        "publisher": "University of California Statewide Integrated Pest Management Program",
        "url": "https://ipm.ucanr.edu/home-and-landscape/less-toxic-insecticides/",
        "source_type": "extension",
    },
    {
        "id": "source-rhs-houseplants",
        "title": "How to grow houseplants",
        "publisher": "Royal Horticultural Society",
        "url": "https://www.rhs.org.uk/plants/types/houseplants/growing-guide",
        "source_type": "horticultural_society",
    },
    {
        "id": "source-rhs-sap-feeders",
        "title": "Indoor plants: sap feeders",
        "publisher": "Royal Horticultural Society",
        "url": "https://www.rhs.org.uk/biodiversity/indoor-plants-sap-feeding-insects",
        "source_type": "horticultural_society",
    },
]

def seed_encyclopedia(conn: sqlite3.Connection) -> dict[str, int]:
    """Insert starter reference records idempotently; never overwrite reviewed content."""
    now = datetime.now(timezone.utc).isoformat()
    counts = {"pests": 0, "diseases": 0, "treatments": 0, "sources": 0}
    for table, rows in (("pests", PESTS), ("diseases", DISEASES), ("treatments", TREATMENTS)):
        for row in rows:
            columns = list(row.keys())
            placeholders = ", ".join("?" for _ in columns)
            names = ", ".join(columns)
            values = [row[k] for k in columns]
            if table in ("pests", "diseases"):
                values += ["needs_review", now]
                names += ", review_status, updated_at"
                placeholders += ", ?, ?"
            else:
                values += ["medium", "needs_review", now]
                names += ", confidence, review_status, updated_at"
                placeholders += ", ?, ?, ?"
            cursor = conn.execute(
                f"INSERT OR IGNORE INTO {table} ({names}) VALUES ({placeholders})",
                values,
            )
            counts[table] += cursor.rowcount

    for row in SOURCES:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO sources
               (id, title, publisher, url, source_type, accessed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["id"], row["title"], row["publisher"], row["url"], row["source_type"], now),
        )
        counts["sources"] += cursor.rowcount

    # General diagnostic and IPM guidance is linked to the sources that support it.
    links = [
        ("treatment-isolate-inspect", "source-ucipm-houseplant-problems", "isolation, inspection and sanitation"),
        ("treatment-water-wash", "source-ucipm-houseplant-problems", "washing exposed soft-bodied pests"),
        ("treatment-prune-dispose", "source-ucipm-houseplant-problems", "removal and disposal of infested material"),
        ("treatment-growing-media-correction", "source-ucipm-houseplant-problems", "watering, drainage and fungus gnat prevention"),
        ("treatment-insecticidal-soap-oil", "source-ucipm-less-toxic", "contact insecticide categories and label precautions"),
        ("treatment-biological-control", "source-ucipm-fungus-gnats", "biological controls for fungus gnat larvae"),
    ]
    for content_id, source_id, claim in links:
        conn.execute(
            """INSERT OR IGNORE INTO content_references
               (content_type, content_id, reference_id, claim)
               VALUES ('treatment', ?, ?, ?)""",
            (content_id, source_id, claim),
        )

    pest_source_map = {
        "pest-mealybug": "source-ucipm-mealybugs",
        "pest-spider-mites": "source-ucipm-spider-mites",
        "pest-scale-insects": "source-ucipm-scales",
        "pest-fungus-gnats": "source-ucipm-fungus-gnats",
    }
    for pest_id, source_id in pest_source_map.items():
        conn.execute(
            """INSERT OR IGNORE INTO content_references
               (content_type, content_id, reference_id, claim)
               VALUES ('pest', ?, ?, 'identification and management overview')""",
            (pest_id, source_id),
        )
    for pest_id in ("pest-aphids", "pest-thrips", "pest-whiteflies"):
        conn.execute(
            """INSERT OR IGNORE INTO content_references
               (content_type, content_id, reference_id, claim)
               VALUES ('pest', ?, 'source-ucipm-houseplant-problems',
                       'houseplant identification and general management')""",
            (pest_id,),
        )
    for disease_id in DISEASES:
        conn.execute(
            """INSERT OR IGNORE INTO content_references
               (content_type, content_id, reference_id, claim)
               VALUES ('disease', ?, 'source-ucipm-houseplant-problems',
                       'differential diagnosis: houseplant problems')""",
            (disease_id["id"],),
        )
    pest_treatment_map = {
        "pest-mealybug": ["treatment-isolate-inspect", "treatment-water-wash", "treatment-prune-dispose", "treatment-insecticidal-soap-oil", "treatment-biological-control"],
        "pest-spider-mites": ["treatment-isolate-inspect", "treatment-water-wash", "treatment-prune-dispose", "treatment-insecticidal-soap-oil", "treatment-biological-control"],
        "pest-scale-insects": ["treatment-isolate-inspect", "treatment-water-wash", "treatment-prune-dispose", "treatment-insecticidal-soap-oil", "treatment-biological-control"],
        "pest-aphids": ["treatment-isolate-inspect", "treatment-water-wash", "treatment-prune-dispose", "treatment-insecticidal-soap-oil", "treatment-biological-control"],
        "pest-thrips": ["treatment-isolate-inspect", "treatment-water-wash", "treatment-prune-dispose", "treatment-insecticidal-soap-oil", "treatment-biological-control"],
        "pest-whiteflies": ["treatment-isolate-inspect", "treatment-water-wash", "treatment-prune-dispose", "treatment-insecticidal-soap-oil", "treatment-biological-control"],
        "pest-fungus-gnats": ["treatment-isolate-inspect", "treatment-growing-media-correction", "treatment-biological-control"],
    }
    for pest_id, treatment_ids in pest_treatment_map.items():
        for sequence, treatment_id in enumerate(treatment_ids):
            conn.execute(
                """INSERT OR IGNORE INTO pest_treatments(pest_id, treatment_id, sequence)
                   VALUES (?, ?, ?)""",
                (pest_id, treatment_id, sequence),
            )

    disease_treatment_map = {
        "disease-root-rot-complex": ["treatment-isolate-inspect", "treatment-growing-media-correction", "treatment-prune-dispose"],
        "disease-powdery-mildew": ["treatment-isolate-inspect", "treatment-prune-dispose"],
        "disease-botrytis-grey-mould": ["treatment-isolate-inspect", "treatment-prune-dispose"],
        "disease-bacterial-leaf-spot": ["treatment-isolate-inspect", "treatment-prune-dispose"],
        "disease-viral-mosaic": ["treatment-isolate-inspect", "treatment-prune-dispose"],
    }
    for disease_id, treatment_ids in disease_treatment_map.items():
        for sequence, treatment_id in enumerate(treatment_ids):
            conn.execute(
                """INSERT OR IGNORE INTO disease_treatments(disease_id, treatment_id, sequence)
                   VALUES (?, ?, ?)""",
                (disease_id, treatment_id, sequence),
            )

    return counts
