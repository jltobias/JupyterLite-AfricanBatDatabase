# Spatial method

## Coordinate validation

Bat geometries and USGS critical-mineral point geometries are read in WGS 84 (EPSG:4326). Geographic coordinates outside longitude [-180, 180] or latitude [-90, 90], non-finite coordinates, and invalid sentinel values are excluded. The original valid point precision is preserved in the exported GeoJSON.

USGS 2006 decimal-degree facility fields are parsed as numeric coordinates and validated against the same ranges. The 2017 shapefile's point layer is filtered to countries represented in the bat dataset; country-name variants are normalized for matching. Source names, country, commodity, deposit type, and coordinates are carried through where present. Because the 2017 data mix mines, deposits, districts, and regions without a per-feature class field, those points are labeled as unclassified critical-mineral resource features. Kibali Gold Mine is a separate Wikidata-sourced point because it is absent from both USGS sources.

## Distance matching

For each coordinate-valid 2006 facility classified as a mine, 2017 resource feature, and supplemental mine point, the analysis calculates WGS 84 ellipsoidal geodesic distance to each bat record. The analysis includes records at or inside 50 km, with exact boundaries assigned to the inner band:

| Distance from facility | Band |
|---:|---|
| 0–1 km | 1 km |
| >1–5 km | 5 km |
| >5–10 km | 10 km |
| >10–20 km | 20 km |
| >20–30 km | 30 km |
| >30–40 km | 40 km |
| >40–50 km | 50 km |

These are distance bands from the **selected location**, not ecological foraging ranges.

## JupyterGIS buffer layers

The native JupyterGIS story includes seven optional polygon layers centered on the locations featured in the story. Each layer represents one non-overlapping band (0–1, >1–5, >5–10, >10–20, >20–30, >30–40, or >40–50 km). Boundaries are sampled geodesically at 5-degree azimuth intervals; each feature also records how many bat occurrence records fall in its band. The layers are hidden initially to keep the map readable.

## Bat-centered radii

The standalone StoryMap can draw selected 1, 5, 10, 20, 30, 40, and 50 km circles around the selected location or a selected bat record. Bat-centered circles are generated on demand and displayed for one selected record at a time. These radii are exploratory visualization distances, not a claim that a record is a confirmed roost or that the bat forages to that distance.

## Reproducibility

From the repository root, install `requirements.txt` and run:

```console
python scripts/build_data.py
python -m pytest
```

The build downloads the USGS 2006 table, reads the bundled bat and 2017 USGS shapefiles plus the supplemental Kibali point, and creates data for the StoryMap, JupyterGIS project, and notebooks. See the [JupyterGIS story-map guide](https://jupytergis.readthedocs.io/en/latest/user_guide/how-tos/story-maps.html) for the native project and browser presentation features.
