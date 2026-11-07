"""Import normalized plant reference records from the starter catalog.

Imported records remain needs_review; this is not a claim of species-level
verification. Pest links are added only where the cited sources support them.
"""
from __future__ import annotations
import json
import csv
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from app.catalog import PLANT_CATALOG

# Only records with an individually checked Kew POWO result are marked verified.
# The remainder intentionally stay needs_review until reviewed one by one.
TAXONOMY_OVERRIDES = {
    'plant-016': {
        'accepted_name': 'Philodendron xanadu',
        'submitted_name_synonym': 'Thaumatophyllum xanadu',
        'rank': 'species',
        'parent_name': '',
        'cultivar_epithet': '',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/20011461-1',
    },
    'plant-031': {
        'accepted_name': 'Heptapleurum arboricola',
        'submitted_name_synonym': 'Schefflera arboricola',
        'rank': 'species',
        'parent_name': '',
        'cultivar_epithet': '',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:90845-1',
    },
    'plant-001': {
        'accepted_name': 'Epipremnum aureum',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/87014-1',
    },
    'plant-006': {
        'accepted_name': 'Scindapsus pictus',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/88905-1',
    },
    'plant-008': {
        'accepted_name': 'Monstera deliciosa',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/87478-1',
    },
    'plant-009': {
        'accepted_name': 'Monstera adansonii',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/87464-1',
    },
    'plant-010': {
        'accepted_name': 'Rhaphidophora tetrasperma',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/88594-1',
    },
    'plant-011': {
        'accepted_name': 'Philodendron hederaceum',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/87797-1',
    },
    'plant-020': {
        'accepted_name': 'Zamioculcas zamiifolia',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/89402-1',
    },
    'plant-024': {
        'accepted_name': 'Chlorophytum comosum',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/532810-1',
    },
    'plant-025': {
        'accepted_name': 'Ficus elastica',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:60458499-2',
    },
    'plant-027': {
        'accepted_name': 'Ficus lyrata',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/853158-1',
    },
    'plant-028': {
        'accepted_name': 'Ficus benjamina',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/852486-1',
    },
    'plant-029': {
        'accepted_name': 'Ficus microcarpa',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:853217-1',
    },
    'plant-030': {
        'accepted_name': 'Pachira aquatica',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/179762-2',
    },
    'plant-032': {
        'accepted_name': 'Codiaeum variegatum',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/85073-3',
    },
    'plant-033': {
        'accepted_name': 'Cordyline fruticosa',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:533580-1',
    },
    'plant-034': {
        'accepted_name': 'Dracaena reflexa',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:534338-1',
    },
    'plant-035': {
        'accepted_name': 'Dracaena fragrans',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:534207-1',
    },
    'plant-036': {
        'accepted_name': 'Dracaena sanderiana',
        'rank': 'species',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:60471006-2',
    },
    'plant-022': {
        'accepted_name': 'Dracaena trifasciata',
        'submitted_name_synonym': 'Sansevieria trifasciata',
        'rank': 'species',
        'parent_name': '',
        'cultivar_epithet': '',
        'status': 'verified',
        'source_url': 'https://powo.science.kew.org/taxon/77164235-1',
    },
}


SOURCES = [
 ("source-bmd-bangladesh-seasonal-climate","The Future Climate of Bangladesh","Bangladesh Meteorological Department","https://www.bmd.gov.bd/file/2025/11/20/pdf/195905.pdf","government_meteorological_source","Bangladesh season timing and rainfall/temperature patterns; supports local climate context, not plant-specific seasonal responses."),
 ("source-aspca-canna","Canna — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/canna","toxicology","Lists Canna indica as non-toxic to dogs, cats and horses; does not establish human safety."),
 ("source-aspca-ixora","Flame of the Woods — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/flame-woods","toxicology","Lists Ixora coccinea as non-toxic to dogs, cats and horses; does not establish human safety or cultivar-specific identity."),
 ("source-aspca-gardenia","Gardenia — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/gardenia","toxicology","Lists Gardenia jasminoides as toxic to dogs, cats and horses; principles include geniposide and gardenoside."),
 ("source-aspca-majesty-palm","Majesty Palm — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/majesty-palm","toxicology","Lists Ravenea rivularis as non-toxic to dogs, cats and horses; does not establish human safety."),
 ("source-aspca-lady-palm","Lady Palm — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/lady-palm","toxicology","Lists Rhapis flabelliformis as non-toxic to dogs and cats; does not establish human safety or confirm every Rhapis taxon."),
 ("source-aspca-ponytail-palm","Pony Tail — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/pony-tail","toxicology","Lists Beaucarnea recurvata as non-toxic to dogs, cats and horses; does not establish human safety."),
 ("source-wcvp-v16","WCVP v16 catalog review snapshot","Royal Botanic Gardens, Kew","https://powo.science.kew.org/about-wcvp","taxonomic_backbone","Imported from the local WCVP v16 (2026-06-04) review CSV. Taxonomic snapshot only; cultivar-parent matches do not verify cultivar identity."),
 ('source-aspca-star-jasmine', 'Star Jasmine — Toxic and Non-Toxic Plants', 'ASPCA Animal Poison Control', 'https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/star-jasmine', 'toxicology', 'Lists Trachelospermum jasminoides as non-toxic to dogs, cats and horses; does not establish human safety.'),
 ('source-aspca-cast-iron-plant', 'Cast Iron Plant — Toxic and Non-Toxic Plants', 'ASPCA Animal Poison Control', 'https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/cast-iron-plant', 'toxicology', 'Lists Aspidistra elatior as non-toxic to dogs, cats and horses; does not establish human safety.'),
 ('source-aspca-staghorn-fern', 'Common Staghorn Fern — Toxic and Non-Toxic Plants', 'ASPCA Animal Poison Control', 'https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/common-staghorn-fern', 'toxicology', 'Lists Platycerium bifurcatum as non-toxic to dogs, cats and horses; does not establish human safety.'),
 ('source-aspca-ornamental-plants-2026', 'Flowers and plants and pet safety', 'ASPCA Poison Control', 'https://www.aspca.org/news/do-you-know-which-flowers-and-plants-are-toxic-pets-our-experts-explain', 'toxicology', 'Lists Nephrolepis exaltata, Zinnia elegans and Helianthus as non-toxic to dogs and cats; plant ingestion may still cause mild GI upset.'),
 ("source-ncsu-tradescantia","Tradescantia — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/tradescantia/","extension","Genus-level identification and cultural context; use only for the named Tradescantia entries and supported traits."),
 ("source-rhs-fittonia","Fittonia — RHS Plant Guide","Royal Horticultural Society","https://www.rhs.org.uk/plants/fittonia","horticultural_society","Identification, high humidity, filtered light and moisture-retentive but well-drained medium."),
 ("source-smithsonian-hibiscus","Care of Hibiscus rosa-sinensis","Smithsonian Gardens","https://gardens.si.edu/learn/educational-resources/plant-care-sheets/care-of-hibiscus-rosa-sinensis/","botanical_garden","Species-level tropical hibiscus growth, light and pruning; cultivars vary."),
 ("source-ncsu-gardenia","Gardenia — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/gardenia/","extension","Gardenia genus-level identification and cultural preferences; confirm species applicability."),
 ("source-ncsu-jasmine","Jasminum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/jasminum/","extension","Jasmine genus-level habit, light, soil, pruning and common problems; species differ."),
 ("source-ncsu-lantana","Lantana camara — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/lantana-camara/","extension","Species-level identification, cultivation, pest issues and toxicity."),
 ("source-ncsu-oleander","Nerium oleander — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/nerium-oleander/","extension","Species-level identification, cultivation and high-severity toxicity."),
 ("source-ncsu-adenium","Adenium obesum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/adenium-obesum/","extension","Species-level succulent care, propagation, pests and cardiac-glycoside toxicity."),
 ("source-ncsu-catharanthus","Catharanthus roseus — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/catharanthus-roseus/","extension","Species-level culture, identification, pests and vinca-alkaloid toxicity."),
 ("source-ncsu-asparagus-densiflorus","Asparagus densiflorus — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/asparagus-densiflorus-sprengeri-group/common-name/asparagus/","extension","Species/group-level habit, indoor culture, pest issues and toxicity; cultivar differences may apply."),
 ("source-ncsu-asparagus-setaceus","Asparagus setaceus — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/asparagus-setaceus/common-name/feathered-asparagus-fern/","extension","Species-level identification and berry/sap toxicity."),
 ("source-ncsu-syngonium","Syngonium podophyllum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/syngonium-podophyllum/","extension","Species-level identification, culture, pests and calcium-oxalate toxicity."),
 ("source-ncsu-asplenium-nidus","Asplenium nidus — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/asplenium-nidus/","extension","Species-level epiphytic habit, culture, temperature, pests and identification."),
 ("source-ncsu-nephrolepis","Nephrolepis exaltata — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/nephrolepis-exaltata/","extension","Species-level Boston fern culture, humidity, light and watering."),
 ("source-ncsu-phlebodium","Phlebodium aureum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/phlebodium-aureum/","extension","Species-level blue star fern culture, moisture, humidity, propagation and problems."),
 ("source-ncsu-adiantum","Adiantum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/adiantum/","extension","Genus-level maidenhair fern features and shade context; individual species may differ."),
 ("source-ncsu-platycerium-bifurcatum","Platycerium bifurcatum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/platycerium-bifurcatum/","extension","Species-level staghorn fern epiphytic habit, potting, moisture, light and propagation."),
 ("source-ncsu-pilea","Pilea peperomioides — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/pilea-peperomioides/common-name/chinese-money-plant/","extension","Species-level identification, light and moist, well-drained medium."),
 ("source-ncsu-aspidistra","Aspidistra elatior — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/aspidistra-elatior/","extension","Species-level shade preference, rhizomes and identification."),
 ("source-ncsu-strelitzia","Strelitzia reginae — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/strelitzia-reginae/","extension","Species-level growth, culture, propagation, pests and ingestion toxicity."),
 ("source-ncsu-beaucarnea","Beaucarnea recurvata — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/beaucarnea-recurvata/","extension","Species-level ponytail palm culture, watering, light and identification."),
 ("source-ncsu-ixora","Ixora coccinea — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/ixora-coccinea/","extension","Species-level identification, light, soil, temperature, pruning and propagation."),
 ("source-ncsu-rhapis","Rhapis excelsa — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/rhapis-excelsa/","extension","Species-level lady palm identification and cultivation."),
 ("source-ncsu-gardenia-jasminoides","Gardenia jasminoides — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/gardenia-jasminoides/","extension","Species-level gardenia care, identification, propagation, pests and toxicity."),
 ("source-ncsu-trachelospermum","Trachelospermum jasminoides — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/trachelospermum-jasminoides/","extension","Species-level star jasmine identification, cultivation, pruning and propagation; distinct from Jasminum."),
 ("source-ncsu-pentas","Pentas lanceolata — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/pentas-lanceolata/common-name/pentas/","extension","Species-level pentas light, soil and growth habit."),
 ("source-ncsu-hibiscus-rosa-sinensis","Hibiscus rosa-sinensis — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/hibiscus-rosa-sinensis/common-name/hibiscus/","extension","Species-level tropical hibiscus culture, pruning, propagation and identification."),
 ("source-ncsu-tagetes","Tagetes — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/tagetes/","extension","Genus-level marigold culture, identification and phototoxic irritation; species differ."),
 ("source-ncsu-zinnia","Zinnia elegans — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/zinnia-elegans/","extension","Species-level zinnia culture and identification."),
 ("source-ncsu-cosmos","Cosmos bipinnatus — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/cosmos-bipinnatus/","extension","Species-level cosmos habit, flower traits and reseeding."),
 ("source-ncsu-celosia","Celosia argentea — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/celosia-argentea/","extension","Species-level celosia culture, cultivar-group flower forms and common problems."),
 ("source-ncsu-sunflower","Helianthus — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/helianthus/","extension","Genus-level sunflower culture and notes that include H. annuus; some traits vary by species."),
 ("source-ufas-jatropha","Jatropha integerrima: Peregrina","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/ST319","extension","Species-level Jatropha integerrima morphology, landscape culture, pruning and propagation."),
 ("source-nparks-jatropha","Jatropha integerrima","National Parks Board Singapore","https://www.nparks.gov.sg/florafaunaweb/flora/2/1/2152","government_botanical_database","Species-level toxicity, sap irritation, light, water and propagation."),
 ("source-aspca-areca-palm","Areca palm — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/areca-palm","toxicology","Lists Dypsis lutescens as non-toxic to dogs, cats and horses; does not establish human safety."),
 ("source-aspca-parlor-palm","Parlor palm — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/parlor-palm","toxicology","Lists Chamaedorea elegans as non-toxic to dogs and cats; does not establish human safety."),
 ("source-aspca-boston-fern","Boston fern — Toxic and Non-Toxic Plants","ASPCA Animal Poison Control","https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/boston-fern","toxicology","Lists Nephrolepis exaltata bostoniensis as non-toxic to cats and dogs; does not establish safety for humans or other fern taxa."),
 ("source-ncsu-annual-ornamentals","Herbaceous Ornamentals — Extension Gardener Handbook","North Carolina State Extension","https://content.ces.ncsu.edu/extension-gardener-handbook/10-herbaceous-ornamentals","extension","General annual-flower pruning and cultivation context; not a substitute for species-specific care."),
 ("source-ncsu-houseplant-container","Plants Grown in Containers — Extension Gardener Handbook","North Carolina State Extension","https://content.ces.ncsu.edu/extension-gardener-handbook/18-plants-grown-in-containers","extension","Container selection and broad plant-group context only; not species-specific care."),
 ("source-rhs-houseplants","How to grow houseplants","Royal Horticultural Society","https://www.rhs.org.uk/plants/types/houseplants/growing-guide","horticultural_society",""),
 ("source-powo","Plants of the World Online","Royal Botanic Gardens, Kew","https://powo.science.kew.org/","taxonomic_backbone","Accepted names and synonymy checked for the individually cited records only."),
 ("source-rhs-feeding","How to feed plants","Royal Horticultural Society","https://www.rhs.org.uk/garden-jobs/nutrition-feeding-plants","horticultural_society","General feeding principles only; not species-specific fertilizer type, dose or schedule."),
 ("source-rhs-sap-feeders","Indoor plants: sap feeders","Royal Horticultural Society","https://www.rhs.org.uk/biodiversity/indoor-plants-sap-feeding-insects","horticultural_society",""),
 ("source-umn-hibiscus","Hibiscus","University of Minnesota Extension","https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/hibiscus","extension",""),
 ("source-umn-peppers","Growing peppers","University of Minnesota Extension","https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/growing-peppers","extension",""),
 ("source-commons-pothos-1","Money plant (Epipremnum aureum)","Wikimedia Commons","https://commons.wikimedia.org/wiki/File:Money_plant(Epipremnum_Aureum).jpg","image_license","Author: Mithun Mijar; CC BY-SA 4.0"),
 ("source-commons-pothos-2","Money plant (Epipremnum aureum)","Wikimedia Commons","https://commons.wikimedia.org/wiki/File:Money_plant_(Epipremnum_aureum).jpg","image_license","Author: Mokkie; CC BY-SA 3.0"),
 ("source-commons-pothos-3","Epipremnum aureum","Wikimedia Commons","https://commons.wikimedia.org/wiki/File:Epipremnum_aureum_(405626861).jpg","image_license","Author: Dinesh Valke; CC BY-SA 2.0"),
 ("source-kew-epipremnum","Epipremnum aureum — general information","Royal Botanic Gardens, Kew","https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:87014-1/general-information","botanical_database","Native range and growth habit."),
 ("source-ncsu-epipremnum","Epipremnum aureum","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/epipremnum-aureum/","extension","Identification, cultivation, pests and toxicity."),
 ("source-wi-pothos","Pothos, Epipremnum aureum","University of Wisconsin–Madison Extension","https://hort.extension.wisc.edu/articles/pothos-epipremmum-aureum/","extension","Propagation and cultivar characteristics."),
 ("source-rhs-epipremnum","Epipremnum","Royal Horticultural Society","https://www.rhs.org.uk/plants/epipremnum","horticultural_society","Indoor light and watering guidance."),
 ("source-clemson-pothos","How to Grow Pothos Indoors","Clemson Cooperative Extension","https://hgic.clemson.edu/factsheet/how-to-grow-pothos-indoors-epipremnum-spp-care-cultivars-and-common-problems/","extension","Indoor growing guidance; review the source's geographic context."),
 ("source-nybg-pothos","Pothos (Epipremnum aureum)","New York Botanical Garden","https://libguides.nybg.org/pothos","botanical_garden","Light, watering and humidity context."),
 ("source-nparks-epipremnum","Epipremnum aureum","National Parks Board Singapore","https://www.nparks.gov.sg/florafaunaweb/flora/1/3/1390","government_botanical_database","Plant features, propagation and ingestion/sap hazard."),
 ("source-ufifas-cultivars","New Florida Foliage Plant Cultivar: Pothos ‘Pearls and Jade’","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/EP441/pdf","extension","Cultivar descriptions for common pothos selections."),
 ("source-nparks-scindapsus","Scindapsus pictus","National Parks Board Singapore","https://www.nparks.gov.sg/florafaunaweb/flora/6/0/6027","government_botanical_database","Plant features, habitat and cultivation."),
 ("source-rhs-scindapsus","Scindapsus pictus","Royal Horticultural Society","https://www.rhs.org.uk/plants/93929/scindapsus-pictus-v/details","horticultural_society","Native range, cultivation and propagation."),
 ("source-ncsu-scindapsus","Silver Pothos — Scindapsus pictus","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/scindapsus-pictus/common-name/silver-pothos/","extension","Identification and cultivar names."),
 ("source-umn-monstera","Monstera deliciosa","University of Minnesota Extension","https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/propagating-monstera-deliciosa","extension","Propagation, node requirements and watering."),
 ("source-ncsu-monstera","Monstera deliciosa","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/monstera-deliciosa/","extension","Identification, growing conditions and toxicity."),
 ("source-rhs-adansonii","Monstera adansonii","Royal Horticultural Society","https://www.rhs.org.uk/plants/11191/monstera-adansonii/details","horticultural_society","Cultivation, propagation and hazard."),
 ("source-ncsu-rhaphidophora","Rhaphidophora tetrasperma","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/rhaphidophora-tetrasperma/","extension","Identification, cultivation, pests and toxicity."),
 ("source-ncsu-philodendron-hederaceum","Philodendron hederaceum","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/philodendron-hederaceum/","extension","Species identification, culture and toxicity."),
 ("source-rhs-philodendron","How to grow philodendrons","Royal Horticultural Society","https://www.rhs.org.uk/plants/philodendron/growing-guide","horticultural_society","Genus-level cultivation guidance only."),
 ("source-uconn-philodendron","Philodendron","University of Connecticut Extension","https://homegarden.cahnr.uconn.edu/FactSheets/philodendron/","extension","Genus-level care and cultivar Brasil identification."),
 ("source-ncsu-birkin","Philodendron 'Birkin'","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/philodendron-birkin/","extension","Cultivar appearance and growing problems."),
 ("source-nparks-pink-princess","Philodendron 'Pink Princess'","National Parks Board Singapore","https://www.nparks.gov.sg/florafaunaweb/flora/8/5/8541","government_botanical_database","Cultivar identification, care, propagation and hazard."),
 ("source-nparks-erubescens","Philodendron erubescens","National Parks Board Singapore","https://www.nparks.gov.sg/florafaunaweb/flora/1/4/1475","government_botanical_database","Parent species growth form and native distribution."),
 ("source-ncsu-heptapleurum","Heptapleurum arboricola","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/heptapleurum-arboricola/","extension","Dwarf umbrella tree identification, cultivation and toxicity."),
 ("source-ifas-xanadu","Philodendron x 'Xanadu'","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/FP474/about","extension","Cultivar identity and landscape characteristics."),
 ("source-clemson-aglaonema","Chinese Evergreen (Aglaonema)","Clemson Cooperative Extension","https://hgic.clemson.edu/factsheet/chinese-evergreen-aglaonema-care-cultivation-growing-guide/","extension","Care and cultivar background."),
 ("source-ifas-aglaonema","Aglaonema spp.","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/FP025","extension","Morphology, culture and toxicity."),
 ("source-ncsu-dieffenbachia","Dieffenbachia seguine","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/dieffenbachia-seguine/","extension","Identification, culture, propagation, pests and safety."),
 ("source-iastate-zz","ZZ plant care","Iowa State University Extension","https://yardandgarden.extension.iastate.edu/faq/i-recently-purchased-zz-plant-how-do-i-care-it","extension","Care, propagation and toxicity."),
 ("source-uconn-zz","ZZ plant","University of Connecticut Extension","https://homegarden.cahnr.uconn.edu/factsheets/zz-plant/","extension","Propagation, toxicity and Raven cultivar distinction."),
 ("source-ifas-zz","Cultural Guidelines for Commercial Production of Interiorscape ZZ","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/EP252","extension","Production, low-light tolerance and propagation."),
 ("source-ncsu-snake","Dracaena trifasciata","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/dracaena-trifasciata/","extension","Identification, cultivation and cultivar descriptions."),
 ("source-ncsu-spider","Chlorophytum comosum","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/chlorophytum-comosum/","extension","Identification, culture and propagation."),
 ("source-wi-spider","Spider plant","University of Wisconsin–Madison Extension","https://hort.extension.wisc.edu/articles/spider-plant-chlorophytum-comosum/","extension","Cultivar characteristics and propagation."),
 ("source-ifas-rubber","Ficus elastica: Rubber Tree","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/ST252","extension","Culture, propagation, cultivars and pests."),
 ("source-ncsu-ficus-lyrata","Ficus lyrata","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/ficus-lyrata/","extension","Identification, culture and toxicity."),
 ("source-ncsu-ficus-microcarpa","Ficus microcarpa 'Ginseng'","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/ficus-microcarpa-ginseng/","extension","Bonsai form, aerial roots and cultivation."),
 ("source-clemson-ficus-benjamina","Weeping Ficus","Clemson Cooperative Extension","https://hgic.clemson.edu/factsheet/weeping-ficus/","extension","Habit, light and indoor care."),
 ("source-ncsu-pachira","Pachira aquatica","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/pachira-aquatica/","extension","Money tree description and toxicity."),
 ("source-ncsu-croton","Codiaeum variegatum","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/codiaeum-variegatum/","extension","Croton light, water and foliage characteristics."),
 ("source-ncsu-cordyline","Cordyline fruticosa","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/cordyline-fruticosa/","extension","Ti plant features and toxicity."),
 ("source-ncsu-dracaena-reflexa","Dracaena reflexa var. reflexa","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/dracaena-reflexa-var-reflexa/","extension","Song of India growth and cultivation."),
 ("source-ncsu-dracaena-fragrans","Dracaena fragrans","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/dracaena-fragrans/","extension","Corn plant care, propagation, pests and toxicity."),
 ("source-ncsu-dracaena-sanderiana","Dracaena sanderiana","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/dracaena-sanderiana/","extension","Lucky bamboo cultivation and toxicity."),
 ("source-ncsu-caladium","Caladium bicolor","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/caladium-bicolor/","extension","Tuberous growth, seasonal care and toxicity."),
 ("source-ufas-alocasia","Alocasia spp.","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/FP033/about","extension","Genus-level cultivation; not cultivar-specific."),
 ("source-ncsu-alocasia","Alocasia","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/alocasia/","extension","Genus and species characteristics."),
 ("source-ncsu-colocasia","Colocasia esculenta","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/colocasia-esculenta/","extension","Taro habit, moisture needs and toxicity."),
 ("source-ncsu-orbifolia","Goeppertia orbifolia","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/goeppertia-orbifolia/","extension","Humidity, moisture and water-quality guidance."),
 ("source-ncsu-insignis","Goeppertia insignis","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/goeppertia-insignis/","extension","Rattlesnake plant identification."),
 ("source-ncsu-ornata","Goeppertia ornata","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/goeppertia-ornata/","extension","Pinstripe plant identification and cultivation."),
 ("source-ncsu-maranta","Maranta leuconeura","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/maranta-leuconeura/","extension","Prayer plant identification and care."),
 ("source-ncsu-peperomia-obtusifolia","Peperomia obtusifolia","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/peperomia-obtusifolia/","extension","Watering, light, pests and identification."),
 ("source-ncsu-peperomia-argyreia","Peperomia argyreia","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/peperomia-argyreia/","extension","Watermelon peperomia leaf pattern and care."),
 ("source-umn-hypoestes","Polka dot plant","University of Minnesota Extension","https://extension.umn.edu/houseplants/polka-dot-plant","extension","General care and propagation; check availability."),
 ("source-ncsu-coleus","Coleus scutellarioides","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/coleus-scutellarioides/","extension","Coleus habit, light and propagation."),
 ("source-ncsu-tradescantia-pallida","Tradescantia pallida","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/tradescantia-pallida/","extension","Purple heart growth, propagation and irritation."),
 ("source-ncsu-xanadu","Philodendron xanadu","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/philodendron-xanadu/","extension","Species identity, habit and cultivation."),
 ("source-ncsu-crossandra","Crossandra infundibuliformis — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/crossandra-infundibuliformis/common-name/crossandra/","extension","Species-level identification, indoor culture, humidity and propagation."),
 ("source-ncsu-zephyranthes-candida","Zephyranthes candida — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/zephyranthes-candida/","extension","Species-level rain lily identification, light, seasonal care and propagation."),
 ("source-ncsu-canna-indica","Canna indica — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/canna-indica/common-name/canna/","extension","Species-level arrowroot/canna culture, propagation, seasonal care and common problems."),
 ("source-ncsu-hymenocallis","Hymenocallis — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/hymenocallis/common-name/spider-lily/","extension","Genus-level spider lily culture and bulb toxicity; apply cautiously to H. littoralis."),
 ("source-nparks-tabernaemontana","Tabernaemontana divaricata — Flora & Fauna Web","National Parks Board Singapore","https://www.nparks.gov.sg/FloraFaunaWeb/Flora/2/4/2488","government_botanical_database","Species-level pinwheel flower growth form, light, water and soil preferences; no toxicity assessment."),
 ("source-nparks-tabernaemontana-dwarf","Tabernaemontana divaricata (dwarf) — Flora & Fauna Web","National Parks Board Singapore","https://www.nparks.gov.sg/florafaunaweb/flora/4/7/4773","government_botanical_database","Dwarf form identification and basic culture; cultivar identity should still be checked against the user's plant."),
 ("source-ncsu-chamaedorea","Chamaedorea elegans — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/chamaedorea-elegans/","extension","Species-level parlor palm indoor light, watering and humidity guidance."),
 ("source-ifas-dypsis","Dypsis lutescens — UF/IFAS Extension","University of Florida IFAS Extension","https://ask.ifas.ufl.edu/publication/ST165","extension","Species-level areca palm landscape culture and soil requirements."),
 ("source-ncsu-impatiens-walleriana","Impatiens walleriana — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/impatiens-walleriana/","extension","Species-level impatiens culture, propagation, common problems and seasonality."),
 ("source-ncsu-impatiens-hawkeri","Impatiens hawkeri — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/impatiens-hawkeri/common-name/new-guinea-impatiens/","extension","Species-level New Guinea impatiens identification and culture."),
 ("source-ncsu-impatiens-balsamina","Impatiens balsamina — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/impatiens-balsamina/","extension","Species-level garden balsam identification, culture, self-seeding and low-severity toxicity."),
 ("source-ifas-ravenea","Ravenea rivularis — Extension care sheet","UF/IFAS Santa Rosa County Extension","https://sfyl.ifas.ufl.edu/media/sfylifasufledu/santa-rosa/docs/pdfs/demo-garden-4/Majestic-Palm.pdf","extension","Species-level majesty palm indoor light, warmth and humidity summary."),

 ("source-ncsu-tradescantia-zebrina","Tradescantia zebrina — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/tradescantia-zebrina/common-name/zebra-plant/","extension","Species-level zebra plant identification, care, propagation, common problems and irritation/toxicity notes."),
 ("source-ncsu-adiantum-raddianum","Adiantum raddianum — Plant Toolbox","North Carolina State Extension","https://plants.ces.ncsu.edu/plants/adiantum-raddianum/common-name/maidenhair-fern/","extension","Species-level Delta maidenhair identification, shade, moisture, humidity and common problems."),
 ("source-kstate-maidenhair","Maidenhair Fern — Indoor Plant Care","Kansas State University Research and Extension","https://hnr.k-state.edu/extension/horticulture-resource-center/publications/publications/houseplants/Fern%20Maidenhair.pdf","extension","Genus-level maidenhair humidity, watering, light, fertilizer, pruning and propagation guidance."),

]
IMAGES = [
 ("image-pothos-mithun","https://commons.wikimedia.org/wiki/Special:FilePath/Money_plant(Epipremnum_Aureum).jpg","Money plant / golden pothos","Mithun Mijar","CC BY-SA 4.0","https://commons.wikimedia.org/wiki/File:Money_plant(Epipremnum_Aureum).jpg"),
 ("image-pothos-mokkie","https://commons.wikimedia.org/wiki/Special:FilePath/Money_plant_(Epipremnum_aureum).jpg","Epipremnum aureum","Mokkie","CC BY-SA 3.0","https://commons.wikimedia.org/wiki/File:Money_plant_(Epipremnum_aureum).jpg"),
 ("image-pothos-dinesh","https://commons.wikimedia.org/wiki/Special:FilePath/Epipremnum_aureum_(405626861).jpg","Epipremnum aureum","Dinesh Valke","CC BY-SA 2.0","https://commons.wikimedia.org/wiki/File:Epipremnum_aureum_(405626861).jpg"),
]

def _load_wcvp_v16_overrides() -> dict[str, dict]:
 """Load the checked WCVP snapshot without upgrading cultivar identity."""
 path = Path(__file__).resolve().parent / "data" / "taxonomy" / "wcvp_v16_catalog_review_163.csv"
 if not path.exists():
  return {}
 catalog = {item["id"]: item for item in PLANT_CATALOG}
 result = {}
 with path.open(encoding="utf-8-sig", newline="") as handle:
  for row in csv.DictReader(handle):
   taxon_id = row["catalog_id"].strip()
   plant = catalog.get(taxon_id)
   if plant is None:
    raise ValueError(f"WCVP row references unknown catalog ID: {taxon_id}")
   submitted = " ".join(row["submitted_name"].split())
   current = " ".join(plant["species"].split())
   if submitted.casefold() != current.casefold():
    raise ValueError(f"WCVP name mismatch for {taxon_id}: {submitted!r} != {current!r}")
   match = re.match(r"^(.+?)\s+'([^']+)'$", current)
   outcome = row["review_status"].strip()
   status = {"verified": "verified", "cultivar_parent_only": "needs_review", "unresolved": "unresolved"}.get(outcome)
   if status is None:
    raise ValueError(f"Unexpected WCVP review status for {taxon_id}: {outcome}")
   accepted_name = row["accepted_name"].strip() or submitted
   parent_name = match.group(1) if match else ""
   cultivar_epithet = match.group(2) if match else ""
   rank = "cultivar" if match else row["rank"].strip().casefold() or "species"
   override = {
    "accepted_name": accepted_name,
    "rank": rank,
    "parent_name": parent_name,
    "cultivar_epithet": cultivar_epithet,
    "status": status,
    "source_url": row["powo_url"].strip(),
    "source_id": "source-wcvp-v16",
    "wcvp_review_status": outcome,
    "taxonomy_review_note": row["review_note"].strip(),
   }
   if status == "verified" and not match and accepted_name.casefold() != submitted.casefold():
    override["submitted_name_synonym"] = submitted
   result[taxon_id] = override
 return result

TAXONOMY_OVERRIDES.update(_load_wcvp_v16_overrides())

def _catalog_range_ids(batch: dict) -> list[str]:
 """Expand either an inclusive pair of catalog endpoints or explicit IDs."""
 values = batch.get("catalog_range", [])
 if len(values) == 2:
  first = re.fullmatch(r"(.*?)(\d+)", values[0])
  last = re.fullmatch(r"(.*?)(\d+)", values[1])
  if first and last and first.group(1) == last.group(1):
   start, end = int(first.group(2)), int(last.group(2))
   if end >= start:
    width = max(len(first.group(2)), len(last.group(2)))
    return [f"{first.group(1)}{n:0{width}d}" for n in range(start, end + 1)]
 return values

def _slug(v):
 return re.sub(r"[^a-z0-9]+","-",v.casefold()).strip("-") or "unknown"

def seed_botanical_catalog(conn: sqlite3.Connection) -> dict[str,int]:
 now=datetime.now(timezone.utc).isoformat()
 counts={k:0 for k in ("taxa","names","care_profiles","fertilizer_guides","profile_sections","sources","images","pest_links","disease_links","legacy_ids","synonyms","parent_links")}
 for sid,title,publisher,url,stype,notes in SOURCES:
  cur=conn.execute("INSERT OR IGNORE INTO sources(id,title,publisher,url,source_type,notes) VALUES(?,?,?,?,?,?)",(sid,title,publisher,url,stype,notes)); counts["sources"]+=cur.rowcount
 for p in PLANT_CATALOG:
  taxon=p["id"]; scientific=" ".join(p["species"].split())
  genus=scientific.split()[0]
  override=TAXONOMY_OVERRIDES.get(taxon, {})
  accepted=override.get("accepted_name", scientific)
  submitted_synonym=override.get("submitted_name_synonym", "")
  # Cultivar epithets are parsed as horticultural names, not treated as species names.
  cultivar_match=re.match(r"^(.+?)\s+'([^']+)'$", scientific)
  rank=override.get("rank") or ("cultivar" if cultivar_match else "species")
  parent_name=override.get("parent_name") or (cultivar_match.group(1) if cultivar_match else "")
  cultivar_epithet=override.get("cultivar_epithet") or (cultivar_match.group(2) if cultivar_match else "")
  cur=conn.execute("""INSERT OR IGNORE INTO taxa(id,scientific_name,genus,rank,accepted_name,parent_name,cultivar_epithet,taxonomy_status,taxonomy_source_url,category,description,toxicity,verification_status,created_at,updated_at)
  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(taxon,scientific,genus,rank,accepted,parent_name,cultivar_epithet,override.get("status","needs_review"),override.get("source_url",""),p.get("category",""),p.get("care",""),p.get("toxicity",""),"needs_review",now,now)); counts["taxa"]+=cur.rowcount
  # INSERT OR IGNORE keeps catalog/profile content stable, but it also means
  # newly reviewed taxonomy would never reach an already-seeded database.
  # Refresh only the taxonomy-owned columns when an explicit override exists.
  # Do not reset records without overrides: they may have been reviewed or
  # enriched independently since the previous catalog import.
  if override:
   conn.execute("""UPDATE taxa
   SET accepted_name=?, rank=?, parent_name=?, cultivar_epithet=?,
       taxonomy_status=?, taxonomy_source_url=?
   WHERE id=?""",(
    accepted, rank, parent_name, cultivar_epithet,
    override.get("status","needs_review"), override.get("source_url",""), taxon
   ))
  for legacy_id in p.get("legacy_ids", []):
   counts["legacy_ids"]+=conn.execute("INSERT OR IGNORE INTO taxon_id_aliases(legacy_id,taxon_id,reason) VALUES(?,?,?)",(legacy_id,taxon,"same_submitted_scientific_name")).rowcount
  if submitted_synonym:
   counts["synonyms"]+=conn.execute("INSERT OR IGNORE INTO taxon_names(taxon_id,name,language,name_type,preferred) VALUES(?,?,'en','synonym',0)",(taxon,submitted_synonym)).rowcount
  if override.get("source_url") or override.get("source_id") == "source-wcvp-v16":
   source_id = override.get("source_id", "source-powo")
   claim = ("WCVP v16 result (" + override.get("wcvp_review_status", "checked") + "): "
            + override.get("taxonomy_review_note", "Accepted name checked.")
            if source_id == "source-wcvp-v16"
            else "Accepted name and synonymy checked against Kew POWO: " + accepted + ".")
   conn.execute("INSERT OR IGNORE INTO content_references(content_type,content_id,reference_id,claim) VALUES('taxon',?,?,?)",(taxon,source_id,claim))

  for name,typ,pref in [(p["name"],"common",1)]+[(a,"synonym",0) for a in p.get("aliases",[])]:
   cur=conn.execute("INSERT OR IGNORE INTO taxon_names(taxon_id,name,language,name_type,preferred) VALUES(?,?,'en',?,?)",(taxon,name,typ,pref)); counts["names"]+=cur.rowcount
  cur=conn.execute("""INSERT OR IGNORE INTO care_profiles(taxon_id,light,soil,drainage,watering,notes,confidence,updated_at)
  VALUES(?,?,?,?,?,?,?,?)""",(taxon,p.get("light",""),p.get("soil",""),p.get("drainage",""),"Use the catalog interval only as a prompt to check the growing medium; water according to actual moisture, plant needs and drainage.","Imported from starter catalog. Verify identity and species-specific care before relying on this profile. "+p.get("bangladesh",""),"low",now)); counts["care_profiles"]+=cur.rowcount
  # Import only facts actually present in the source catalog. These are
  # starter values, not species-verified advice; later reviewed batches can
  # replace them with sourced content section by section.
  section_payloads = [
   ("light", "Light", p.get("light", ""), "General starter-catalog light guidance; species-level verification pending."),
   ("watering", "Watering", p.get("drainage", ""), "Starter-catalog watering/drainage prompt; check actual medium moisture."),
   ("soil", "Soil and drainage", p.get("soil", ""), "Starter-catalog growing-medium guidance; species-level verification pending."),
   ("temperature", "Temperature", p.get("temperature", ""), "Starter-catalog temperature range; species-level verification pending."),
   ("humidity", "Humidity", p.get("humidity", ""), "Starter-catalog humidity guidance; species-level verification pending."),
   ("toxicity", "Toxicity and safety", p.get("toxicity", ""), "Starter-catalog toxicity note; verify against authoritative toxicology/veterinary sources."),
  ]
  for section_key, title, content, source_note in section_payloads:
   if content and content.strip():
    conn.execute("""INSERT OR IGNORE INTO taxon_profile_sections
      (taxon_id,section_key,title,content,confidence,review_status,source_note,updated_at)
      VALUES(?,?,?,?,?,?,?,?)""",
      (taxon,section_key,title,content,"low","needs_review",source_note,now))
    # General RHS guidance is attached only as context, never as proof of
    # species-specific claims. Toxicity remains explicitly unsourced here.
    if section_key in {"light","watering","soil"}:
     conn.execute("""INSERT OR IGNORE INTO content_references
       (content_type,content_id,reference_id,claim)
       VALUES('taxon_section',?,?,?)""",
       (f"{taxon}:{section_key}","source-rhs-houseplants",
        "General houseplant context only; not species-specific verification."))

  cat=p.get("category","").casefold()
  if "succulent" in cat or "cactus" in cat:
   ftype="Low-input cactus/succulent fertilizer or a balanced houseplant feed used conservatively."
   active="Feed only during active growth. Avoid routine feeding when growth pauses; do not assume a fixed NPK ratio without species-specific evidence."
  elif "flower" in cat or "herb" in cat:
   ftype="Balanced complete fertilizer appropriate to the plant and growth stage."
   active="Container-grown flowering plants and actively growing herbs may benefit from feeding. Avoid high-phosphorus products unless supported by a demonstrated need or label."
  else:
   ftype="Balanced complete liquid houseplant fertilizer."
   active="Feed only while actively growing and when potting-medium nutrients are becoming depleted. Low-light or slow-growing plants need less."
  fid="fert-"+_slug(taxon)
  cur=conn.execute("""INSERT OR IGNORE INTO fertilizer_guides(id,taxon_id,title,fertilizer_type,active_growth_guidance,dormant_season_guidance,deficiency_signs,excess_signs,application_notes,confidence,updated_at)
  VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(fid,taxon,"Conservative feeding guidance",ftype,active,"Reduce or pause feeding when growth slows; in warm climates use observed growth rather than assuming a cold-winter dormancy.","Yellowing or weak growth has many possible causes; check watering, roots, light, pests and pH before assuming deficiency.","Overfeeding can cause salt accumulation, root injury, leaf-edge burn and soft growth more vulnerable to pests.","Follow the product label, start conservatively, never apply to dry rootballs, and do not feed a stressed or waterlogged plant. General guidance awaiting species-level review.","low",now)); counts["fertilizer_guides"]+=cur.rowcount
  conn.execute("INSERT OR IGNORE INTO content_references(content_type,content_id,reference_id,claim) VALUES('taxon',?,?,?)",(taxon,"source-rhs-houseplants","General houseplant growing context; not species-level verification."))
  conn.execute("INSERT OR IGNORE INTO content_references(content_type,content_id,reference_id,claim) VALUES('fertilizer',?,?,?)",(fid,"source-rhs-feeding","General feeding principles; species-specific timing and dosage not verified."))
 # Resolve cultivar parents only when the exact parent species is present in this catalog.
 # A missing parent is left NULL rather than guessed (e.g. genus-only trade cultivar names).
 for cultivar in conn.execute("SELECT id,parent_name FROM taxa WHERE rank='cultivar' AND parent_name!=''").fetchall():
  parent=conn.execute("SELECT id FROM taxa WHERE id!=? AND (scientific_name=? OR accepted_name=?) ORDER BY id LIMIT 1",(cultivar[0],cultivar[1],cultivar[1])).fetchone()
  if parent:
   counts["parent_links"]+=conn.execute("UPDATE taxa SET parent_taxon_id=? WHERE id=? AND (parent_taxon_id IS NULL OR parent_taxon_id!=?)",(parent[0],cultivar[0],parent[0])).rowcount
 # Source-grounded host/problem relationships only. Taxon IDs checked against catalog.
 links=[
  ("plant-001","pest-mealybug","broad_houseplant_context","RHS lists mealybugs among common indoor-plant sap feeders; not a species-exclusive host record."),
  ("plant-001","pest-scale-insects","broad_houseplant_context","RHS lists scale insects among common indoor-plant sap feeders; confirm on the plant."),
  ("plant-001","pest-spider-mites","broad_houseplant_context","RHS lists glasshouse red spider mite among indoor-plant sap feeders; confirm on the plant."),
  ("plant-001","pest-thrips","broad_houseplant_context","RHS lists thrips among indoor-plant sap feeders; confirm on the plant."),
  ("plant-001","pest-aphids","broad_houseplant_context","RHS lists aphids among indoor-plant sap feeders; confirm on the plant."),
  ("plant-001","pest-fungus-gnats","container_association","RHS lists sciarid flies as a common houseplant pest; moist media is a key context."),
  ("plant-073","pest-aphids","documented_host","UMN Extension identifies aphids as a common hibiscus pest."),
  ("plant-073","pest-spider-mites","documented_host","UMN Extension identifies spider mites as a common hibiscus pest."),
  ("plant-160","pest-aphids","documented_host","UMN Extension identifies aphids as a pest of pepper plants."),
  ("plant-160","disease-bacterial-leaf-spot","documented_problem","UMN Extension describes bacterial spot as a pepper disease."),
  ("plant-160","disease-viral-mosaic","documented_problem","UMN Extension describes virus symptoms in pepper; this is not a specific virus diagnosis."),
 ]
 for taxon,problem,rel,notes in links:
  is_pest=problem.startswith("pest-"); table="taxon_pests" if is_pest else "taxon_diseases"; key="pest_id" if is_pest else "disease_id"
  cur=conn.execute(f"INSERT OR IGNORE INTO {table}(taxon_id,{key},relationship,notes) VALUES(?,?,?,?)",(taxon,problem,rel,notes))
  counts["pest_links" if is_pest else "disease_links"]+=cur.rowcount
 for taxon,source,claim in [("plant-001","source-rhs-sap-feeders","General indoor-plant sap-feeder context."),("plant-073","source-umn-hibiscus","Extension source lists aphids and spider mites as common hibiscus pests."),("plant-160","source-umn-peppers","Extension source documents aphids, bacterial spot and viral symptoms in peppers.")]:
  conn.execute("INSERT OR IGNORE INTO content_references(content_type,content_id,reference_id,claim) VALUES('taxon',?,?,?)",(taxon,source,claim))
 for idx,img in enumerate(IMAGES):
  iid,url,caption,creator,license_name,source_url=img
  cur=conn.execute("""INSERT OR IGNORE INTO media(id,url,caption,attribution,creator,license,source_url,rights_status,created_at)
  VALUES(?,?,?,?,?,?,?,?,?)""",(iid,url,caption,creator,creator,license_name,source_url,"approved",now)); counts["images"]+=cur.rowcount
  conn.execute("INSERT OR IGNORE INTO taxon_media(taxon_id,media_id,sort_order,is_primary) VALUES('plant-001',?,?,?)",(iid,idx,1 if idx==0 else 0))

 # Apply reviewed content batches after starter content. A reviewed section may
 # replace an imported needs-review placeholder once; repeat seeding is safe.
 batch_dir = Path(__file__).resolve().parent / "data" / "profile_batches"
 legacy_taxon_ids = {
  legacy_id: plant["id"]
  for plant in PLANT_CATALOG
  for legacy_id in plant.get("legacy_ids", [])
 }
 for batch_path in sorted(batch_dir.glob("profile-*.json")) if batch_dir.exists() else []:
  with batch_path.open(encoding="utf-8") as handle:
   batch = json.load(handle)
  shared = batch.get("shared_sections", [])
  batch_taxa = list(batch.get("taxa", {}))
  batch_taxa.extend(taxon_id for taxon_id in _catalog_range_ids(batch)
                    if taxon_id not in batch_taxa)
  processed_batch_taxa = set()
  for batch_taxon in batch_taxa:
   taxon = legacy_taxon_ids.get(batch_taxon, batch_taxon)
   if taxon in processed_batch_taxa:
    continue
   processed_batch_taxa.add(taxon)
   specific = batch.get("taxa", {}).get(batch_taxon, {})
   taxon_sections = list(specific.get("sections", shared))
   if specific.get("identification"):
    taxon_sections = [s for s in taxon_sections if s["key"] != "identification"] + [{
     "key": "identification", "title": "Identification",
     "content": specific["identification"],
     "confidence": specific.get("confidence", "high"),
     "status": specific.get("status", "verified"),
     "sources": specific.get("sources", [])
    }]
   for section in taxon_sections:
    key=section["key"]
    status=section.get("status","needs_review")
    cur=conn.execute("""INSERT INTO taxon_profile_sections
      (taxon_id,section_key,title,content,confidence,review_status,source_note,updated_at)
      VALUES(?,?,?,?,?,?,?,?)
      ON CONFLICT(taxon_id,section_key) DO UPDATE SET
        title=excluded.title,content=excluded.content,confidence=excluded.confidence,
        review_status=excluded.review_status,source_note=excluded.source_note,
        updated_at=excluded.updated_at
      WHERE taxon_profile_sections.review_status IN ('draft','needs_review')
        AND excluded.review_status IN ('verified','draft')
        AND (
          taxon_profile_sections.title IS NOT excluded.title
          OR taxon_profile_sections.content IS NOT excluded.content
          OR taxon_profile_sections.review_status IS NOT excluded.review_status
          OR taxon_profile_sections.confidence IS NOT excluded.confidence
          OR taxon_profile_sections.source_note IS NOT excluded.source_note
        )""",
      (taxon,key,section["title"],section["content"],section.get("confidence","medium"),
       status,"Reviewed profile batch "+batch.get("batch_id","unknown"),now))
    counts["profile_sections"]+=cur.rowcount
    for source_id in section.get("sources", []):
     claim = "Source cited for this profile section."
     if source_id == "source-rhs-feeding":
      claim = "General horticultural feeding principles only; not a species-specific dose or schedule."
     elif source_id == "source-bmd-bangladesh-seasonal-climate":
      claim = "Bangladesh seasonal climate context only; plant response is practical local guidance."
     conn.execute("""INSERT OR IGNORE INTO content_references
       (content_type,content_id,reference_id,claim)
       VALUES('taxon_section',?,?,?)""",
       (f"{taxon}:{key}",source_id,claim))
 return counts
