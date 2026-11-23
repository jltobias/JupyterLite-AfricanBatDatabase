<div align="center">

# African Bats & Mining: A StoryMap

### Exploring where documented bat records and mineral facilities meet across Africa

<a href="#the-storymap"><img src="assets/hero.svg" alt="Illustration of an African mine, bat occurrence points, and distance rings" width="100%"></a>

**JupyterGIS storymap** · reproducible notebooks · open data

</div>

> **Deployment status:** The Book, JupyterLite Lab, and StoryMap are built by GitHub Actions for GitHub Pages. The links will be live after Pages is enabled for GitHub Actions and the first deployment succeeds.

| Explore | Link |
|---|---|---|
| **Jupyter Book** — data, methods, results, and image credits | [Read the book](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/book/) |
| **JupyterLite Lab** — run the analysis notebook in your browser | [Open JupyterLite](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/lab/) |
| **JupyterGIS StoryMap** — step through mine facilities | [Open the StoryMap](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/storymap/) |
| **Native JupyterGIS story** | [Open the `.jGIS` project in JupyterLite](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/lab/index.html?path=african_bat_mines_story.jGIS) |
| **Notebook.link** — open the repository's notebook and files in the browser | [Open this project in Notebook.link](https://notebook.link/github/jltobias/JupyterLite-AfricanBatDatabase/tree/main/) |

## Current build

- **17,285** point records in the supplied shapefile; **17,255** valid coordinates are retained at their original precision, and 30 invalid sentinel coordinates are excluded.
- **848** geocoded USGS facility records in countries represented by the bat-point dataset.
- **289** facilities classified as mines have at least one bat record within 50 km.
- Those mine pages contain **3,292** unique bat records and **6,064** mine-to-record distance matches across **182** scientific names.

The counts are generated from the exact input versions documented below and can be reproduced with `python scripts/build_data.py`.

## The storymap

The experience follows a **mine-to-mine narrative**: each page introduces a coordinate-valid USGS mine with at least one bat point within 50 km, then brings those nearby records into view. The pacing takes inspiration from [Esri's *One World, Many Voices*](https://storymaps.esri.com/stories/endangered-languages/), with original project design. The static StoryMap provides interactive labels, accessible species cards, facility navigation, source-credited photos, and on-demand buffer controls. A native `.jGIS` guided story, source data, and seven toggleable mine-centered distance-band layers are included in JupyterLite.

Each facility page pairs source attributes with a photograph only when a correctly identified and reusable facility image is available. If no site-specific image is verified, it says so rather than misidentifying another mine. Bat photographs are used as species illustrations and are not represented as the animals at a mapped locality. The map:

- Keep the selected facility prominent and show its country, commodity, type, status, mining method, operator, and capacity when recorded.
- Label nearby points by **genus and species**; hover previews a species card and click, tap, or keyboard focus can open it.
- Calculate facility-to-point distances with WGS 84 ellipsoidal geodesics and assign records to non-overlapping bands: 0–1, 1–5, 5–10, 10–20, 20–30, 30–40, and 40–50 km.
- Include those seven geodesic distance bands as separate, initially hidden polygon layers in the native JupyterGIS project. The layers are centered on mines represented in the story and show the corresponding occurrence-record count.
- Let readers draw one or more 1, 5, 10, 20, 30, 40, and 50 km circles from either the selected facility or a selected bat point. Bat-centered circles are rendered on demand to avoid obscuring other points.
- Show English names, diet, foraging information, and disease context only when there is a cited species-level source. A radius chosen for this spatial analysis is not a foraging range.

### A clearer view than an all-labels map

The supplied example shows why every species name and every set of overlapping circles should not be drawn at once. The StoryMap reduces clutter by:

- Showing circles only on demand for the selected point or mine, using thin outlines instead of opaque overlapping fills.
- Using compact, high-contrast species labels in hover tooltips and cards rather than drawing every label permanently.
- Keeping the mine marker visually distinct from bat records, and using a legend that states what each buffer is centered on.
- Putting detailed species traits and photographs in an inspectable popup/story card rather than permanently labeling the map; the card will open on hover, click, tap, or keyboard focus.
- Supporting keyboard and touch interaction as well as hover, with a click-to-open alternative for tooltips.

## Run locally

```console
python -m pip install -r requirements.txt
python scripts/build_data.py
python -m pytest
jupyter-book build book --path-output _build/jbook
```

The GitHub Actions workflow builds the Book, JupyterLite app, and StoryMap and deploys them to Pages on `main`. The root `environment.yml` supports both JupyterLite and Notebook.link; the workflow also installs `specta` so the native `.jGIS` story can be presented in the browser.

## Important interpretation notes

- The USGS source is a **2006 inventory of mineral facilities**—including mines, plants, mills, and refineries—not a current, mine-only operating register. Its coordinates and operating/status details need contextual checking before making site-specific or present-day claims.
- The African Bat Database is an occurrence/locality database. A bat record is **not automatically a confirmed roost**. The analysis should call these “bat records” unless the source or a separately cited source verifies roost use.
- A point within 50 km is a **spatial proximity observation**, not proof of habitat use, ecological interaction, impact, exposure, or causation. The selected distance bands are exploratory, not biological thresholds.
- Foraging range and diet vary by species, population, season, and source. Report species-specific estimates with citations and avoid presenting a single value as universal.
- A reported association between a bat species and a pathogen does **not** show that a nearby mine is a disease source or that people or wildlife are at elevated risk. Disease information must be evidence-based, clearly qualified, and separated from the proximity analysis.
- The user-supplied shapefile's coordinate precision is preserved as requested. Its source layer has no roost-status field, so the map labels points as **bat records**, not verified roosts.

## Data sources

### Bat records

Monadjem, A., Montauban, C., Webala, P. W., Laverty, T. M., Bakwo-Fils, E. M., Torrent, L., Tanshi, I., Kane, A., Rutrough, A. L., Waldien, D. L., & Taylor, P. J. (2024). **African bat database: Curated data of occurrences, distributions and conservation metrics for sub-Saharan bats.** *Scientific Data*, 11, 1309. [https://doi.org/10.1038/s41597-024-04170-7](https://doi.org/10.1038/s41597-024-04170-7).

The map uses the supplied ESRI shapefile derived from the November 2024 CSV:

Monadjem, A. et al. (2024). **African Bat Database**, version 1. Figshare. [https://doi.org/10.6084/m9.figshare.26363308.v1](https://doi.org/10.6084/m9.figshare.26363308.v1). Dataset license: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The later Figshare release adds a `Roost` field, but those records do not match the provided shapefile by species, country, and coordinates. Roost flags are not transferred to other locations.

### Mineral facilities

Eros, J. M., & Candelario-Quintana, L. (2006). **Mineral Facilities of Africa and the Middle East.** U.S. Geological Survey Open-File Report 2006-1135, version 1.0. [Report and Table 1](https://pubs.usgs.gov/of/2006/1135/). Table 1: [Excel file](https://pubs.usgs.gov/of/2006/1135/table1.xls).

### Species ecology and media

Species names, traits, and disease context are linked to species-specific references when available; missing foraging-range values are not invented. **Profile coverage is currently partial:** six of the 182 represented species have profile entries, only a few have sourced diet notes, and quantified foraging ranges or species-specific disease associations have not yet been reviewed. The currently included bat and mine photographs are listed in the [Book's media credits](https://jltobias.github.io/JupyterLite-AfricanBatDatabase/book/media-credits.html). Each image credit identifies its creator, source page, and license.

## Image credits

- **Splash illustration:** Original project illustration (`assets/hero.svg`).
- Bat and mineral-facility photographs: individually credited in [book/media-credits.md](book/media-credits.md).

## Contributing

Contributions are welcome, especially source-verified species ecology, facility data checks, reproducible spatial analysis, accessible map design, and correctly licensed photographs. Please include citations, data versions, and image/license attribution with contributions.

## License

The source datasets retain their own licenses and terms. Project code, documentation, and original artwork will be licensed separately once the repository license is selected. Third-party photographs remain under their respective licenses.
