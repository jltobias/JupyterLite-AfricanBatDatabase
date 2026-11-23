# First reproducible run

The current build uses the user-supplied 2024 African Bat Database point shapefile and USGS Open-File Report 2006-1135 Table 1. The source's full valid coordinate precision is preserved.

- **17,285** point features are in the shapefile; **17,255** have valid point coordinates and **30** invalid sentinel coordinates are excluded.
- **848** geocoded USGS facilities are retained for countries represented in the bat-point dataset.
- **289** facilities classified as mines have at least one point record within 50 km.
- Those mine pages contain **3,292** unique bat point records and **6,064** mine-to-record distance matches.
- **182** scientific names occur in those matched records.

Counts are reproducible build outputs, not ecological estimates. A point may be associated with multiple mine pages, so the record total and distance-match total differ. The exact counts for any publication are shown in the generated [StoryMap data](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/storymap/data/storymap.json).

## What this does not establish

The shapefile has no roost-status field. These are bat occurrence/locality points, and the 1–50 km circles are spatial comparison radii, not measured foraging ranges. Mine proximity alone does not demonstrate roosting, exposure, ecological impact, or disease transmission.
