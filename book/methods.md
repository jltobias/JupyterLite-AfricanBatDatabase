# Spatial method

## Coordinate validation

Bat geometries are read directly from the provided shapefile in WGS 84 (EPSG:4326). Geographic coordinates outside longitude [-180, 180] or latitude [-90, 90], non-finite coordinates, and invalid sentinel values are excluded. The original valid point precision is preserved in the exported GeoJSON.

USGS decimal-degree facility fields are parsed as numeric coordinates and validated against the same ranges. Facility names, source positions, country, type, commodity, mining method, operator, status, capacity, and units are carried through where present.

## Distance matching

For each coordinate-valid facility classified as a mine, the analysis calculates WGS 84 ellipsoidal geodesic distance to each bat record. The analysis includes records at or inside 50 km, with exact boundaries assigned to the inner band:

| Distance from facility | Band |
|---:|---|
| 0–1 km | 1 km |
| >1–5 km | 5 km |
| >5–10 km | 10 km |
| >10–20 km | 20 km |
| >20–30 km | 30 km |
| >30–40 km | 40 km |
| >40–50 km | 50 km |

These are distance bands from the **facility**, not ecological foraging ranges.

## JupyterGIS buffer layers

The native JupyterGIS story includes seven optional polygon layers centered on the mines featured in the story. Each layer represents one non-overlapping band (0–1, >1–5, >5–10, >10–20, >20–30, >30–40, or >40–50 km). Boundaries are sampled geodesically at 5-degree azimuth intervals; each feature also records how many bat occurrence records fall in its band. The layers are hidden initially to keep the map readable.

## Bat-centered radii

The standalone StoryMap can draw selected 1, 5, 10, 20, 30, 40, and 50 km circles around the selected mine or a selected bat record. Bat-centered circles are generated on demand and displayed for one selected record at a time. These radii are exploratory visualization distances, not a claim that a record is a confirmed roost or that the bat forages to that distance.

## Reproducibility

From the repository root, install `requirements.txt` and run:

```console
python scripts/build_data.py
python -m pytest
```

The build downloads the USGS table, reads the bundled shapefile, and creates the data used by the StoryMap, JupyterGIS project, and notebooks. See the [JupyterGIS story-map guide](https://jupytergis.readthedocs.io/en/latest/user_guide/how-tos/story-maps.html) for the native project and browser presentation features.
