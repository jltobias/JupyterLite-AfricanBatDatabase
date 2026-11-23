# Reproducible spatial results

The current build uses the user-supplied 2024 African Bat Database point shapefile, USGS Open-File Report 2006-1135 Table 1, the supplied [2017 USGS critical-mineral point layer](https://www.sciencebase.gov/catalog/item/594d3c8ee4b062508e39b332) ([DOI](https://doi.org/10.5066/F7GH9GQR)), and a separately attributed supplemental point for Kibali Gold Mine. Source coordinate precision is preserved.

- **17,285** point features are in the shapefile; **17,255** have valid point coordinates and **30** invalid sentinel coordinates are excluded.
- **848** geocoded facilities are retained from the USGS 2006 inventory.
- **232** USGS critical-mineral point features and **one supplemental Kibali location** are included.
- **290** mine pages and **195** resource-feature pages have at least one bat record within 50 km.
- Those **485** location pages contain **4,387** unique bat point records and **10,340** location-to-record distance matches.
- **207** scientific names occur in those matched records.

Counts are reproducible build outputs, not ecological estimates. The 2017 USGS source covers selected mines, deposits, districts, and regions but does not classify each feature; it is not a 2026 mine inventory. A bat point may be associated with multiple location pages, so the record total and distance-match total differ. The exact counts for any publication are shown in the generated [StoryMap data](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/storymap/data/storymap.json).

## What this does not establish

The shapefile has no roost-status field. These are bat occurrence/locality points, and the 1–50 km circles are spatial comparison radii, not measured foraging ranges. Mine proximity alone does not demonstrate roosting, exposure, ecological impact, or disease transmission.
