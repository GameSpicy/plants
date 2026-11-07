"""Import normalized plant reference records from the starter catalog.

Imported records remain needs_review; this is not a claim of species-level
verification. Pest links are added only where the cited sources support them.
"""
from __future__ import annotations
import re
import sqlite3
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
 ("source-rhs-houseplants","How to grow houseplants","Royal Horticultural Society","https://www.rhs.org.uk/plants/types/houseplants/growing-guide","horticultural_society",""),
 ("source-powo","Plants of the World Online","Royal Botanic Gardens, Kew","https://powo.science.kew.org/","taxonomic_backbone","Accepted names and synonymy checked for the individually cited records only."),
 ("source-rhs-feeding","How to feed plants","Royal Horticultural Society","https://www.rhs.org.uk/garden-jobs/nutrition-feeding-plants","horticultural_society",""),
 ("source-rhs-sap-feeders","Indoor plants: sap feeders","Royal Horticultural Society","https://www.rhs.org.uk/biodiversity/indoor-plants-sap-feeding-insects","horticultural_society",""),
 ("source-umn-hibiscus","Hibiscus","University of Minnesota Extension","https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/hibiscus","extension",""),
 ("source-umn-peppers","Growing peppers","University of Minnesota Extension","https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/growing-peppers","extension",""),
 ("source-commons-pothos-1","Money plant (Epipremnum aureum)","Wikimedia Commons","https://commons.wikimedia.org/wiki/File:Money_plant(Epipremnum_Aureum).jpg","image_license","Author: Mithun Mijar; CC BY-SA 4.0"),
 ("source-commons-pothos-2","Money plant (Epipremnum aureum)","Wikimedia Commons","https://commons.wikimedia.org/wiki/File:Money_plant_(Epipremnum_aureum).jpg","image_license","Author: Mokkie; CC BY-SA 3.0"),
 ("source-commons-pothos-3","Epipremnum aureum","Wikimedia Commons","https://commons.wikimedia.org/wiki/File:Epipremnum_aureum_(405626861).jpg","image_license","Author: Dinesh Valke; CC BY-SA 2.0"),
]
IMAGES = [
 ("image-pothos-mithun","https://commons.wikimedia.org/wiki/Special:FilePath/Money_plant(Epipremnum_Aureum).jpg","Money plant / golden pothos","Mithun Mijar","CC BY-SA 4.0","https://commons.wikimedia.org/wiki/File:Money_plant(Epipremnum_Aureum).jpg"),
 ("image-pothos-mokkie","https://commons.wikimedia.org/wiki/Special:FilePath/Money_plant_(Epipremnum_aureum).jpg","Epipremnum aureum","Mokkie","CC BY-SA 3.0","https://commons.wikimedia.org/wiki/File:Money_plant_(Epipremnum_aureum).jpg"),
 ("image-pothos-dinesh","https://commons.wikimedia.org/wiki/Special:FilePath/Epipremnum_aureum_(405626861).jpg","Epipremnum aureum","Dinesh Valke","CC BY-SA 2.0","https://commons.wikimedia.org/wiki/File:Epipremnum_aureum_(405626861).jpg"),
]
def _slug(v):
 return re.sub(r"[^a-z0-9]+","-",v.casefold()).strip("-") or "unknown"

def seed_botanical_catalog(conn: sqlite3.Connection) -> dict[str,int]:
 now=datetime.now(timezone.utc).isoformat()
 counts={k:0 for k in ("taxa","names","care_profiles","fertilizer_guides","sources","images","pest_links","disease_links","legacy_ids","synonyms")}
 for sid,title,publisher,url,stype,notes in SOURCES:
  cur=conn.execute("INSERT OR IGNORE INTO sources(id,title,publisher,url,source_type,notes) VALUES(?,?,?,?,?,?)",(sid,title,publisher,url,stype,notes)); counts["sources"]+=cur.rowcount
 for p in PLANT_CATALOG:
  taxon=p["id"]; scientific=" ".join(p["species"].split())
  genus=scientific.split()[0]
  override=TAXONOMY_OVERRIDES.get(taxon, {})
  accepted=override.get("accepted_name", scientific)
  submitted_synonym=override.get("submitted_name_synonym", "")
  # Cultivar epithets are parsed as horticultural names, not treated as species names.
  cultivar_match=re.match(r"^(.+?)\\s+'([^']+)'$", scientific)
  rank=override.get("rank") or ("cultivar" if cultivar_match else "species")
  parent_name=override.get("parent_name") or (cultivar_match.group(1) if cultivar_match else "")
  cultivar_epithet=override.get("cultivar_epithet") or (cultivar_match.group(2) if cultivar_match else "")
  cur=conn.execute("""INSERT OR IGNORE INTO taxa(id,scientific_name,genus,rank,accepted_name,parent_name,cultivar_epithet,taxonomy_status,taxonomy_source_url,category,description,toxicity,verification_status,created_at,updated_at)
  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(taxon,scientific,genus,rank,accepted,parent_name,cultivar_epithet,override.get("status","needs_review"),override.get("source_url",""),p.get("category",""),p.get("care",""),p.get("toxicity",""),"needs_review",now,now)); counts["taxa"]+=cur.rowcount
  for legacy_id in p.get("legacy_ids", []):
   counts["legacy_ids"]+=conn.execute("INSERT OR IGNORE INTO taxon_id_aliases(legacy_id,taxon_id,reason) VALUES(?,?,?)",(legacy_id,taxon,"same_submitted_scientific_name")).rowcount
  if submitted_synonym:
   counts["synonyms"]+=conn.execute("INSERT OR IGNORE INTO taxon_names(taxon_id,name,language,name_type,preferred) VALUES(?,?,'en','synonym',0)",(taxon,submitted_synonym)).rowcount
  if override.get("source_url"):
   conn.execute("INSERT OR IGNORE INTO content_references(content_type,content_id,reference_id,claim) VALUES('taxon',?,'source-powo',?)",(taxon,"Accepted name and synonymy checked against Kew POWO: "+accepted+"."))

  for name,typ,pref in [(p["name"],"common",1)]+[(a,"synonym",0) for a in p.get("aliases",[])]:
   cur=conn.execute("INSERT OR IGNORE INTO taxon_names(taxon_id,name,language,name_type,preferred) VALUES(?,?,'en',?,?)",(taxon,name,typ,pref)); counts["names"]+=cur.rowcount
  cur=conn.execute("""INSERT OR IGNORE INTO care_profiles(taxon_id,light,soil,drainage,watering,notes,confidence,updated_at)
  VALUES(?,?,?,?,?,?,?,?)""",(taxon,p.get("light",""),p.get("soil",""),p.get("drainage",""),"Use the catalog interval only as a prompt to check the growing medium; water according to actual moisture, plant needs and drainage.","Imported from starter catalog. Verify identity and species-specific care before relying on this profile. "+p.get("bangladesh",""),"low",now)); counts["care_profiles"]+=cur.rowcount
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
 return counts
