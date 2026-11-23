# Data and coverage

## Bat point records

The project input is the user-supplied [AfricanBatDatabasePoints shapefile](https://figshare.com/articles/dataset/African_Bat_Database/26363308), derived from the African Bat Database 2024 CSV. It contains point geometries in **EPSG:4326** and fields for family, genus, species epithet, museum number, date, year, country, locality, source reference, holotype, and checked status.

The shapefile has no `Roost` attribute. The original points are therefore treated as occurrence/locality records; a filename or GIS layer name is not proof of roost status. Coordinates are kept at their supplied precision. Invalid sentinel coordinates are excluded from spatial calculations.

The 2026 Figshare release adds a roost field, but its roost records do not match the provided 2024 shapefile records by species, country, and coordinate. The project does not transfer those flags to unrelated points.

## Mineral facilities

Eros, J. M., & Candelario-Quintana, L. (2006). *Mineral Facilities of Africa and the Middle East*. U.S. Geological Survey Open-File Report 2006-1135. [Report and Table 1](https://pubs.usgs.gov/of/2006/1135/). The table includes mines and other facilities such as plants, mills, and refineries. The story chapters focus on rows classified as `mine`; the map retains other geocoded facility types for context.

This is a historical inventory, not a current operating register. The project preserves the source's status and facility attributes without asserting that they are current.

## Dataset citation

Monadjem, A., Montauban, C., Webala, P. W., Laverty, T. M., Bakwo-Fils, E. M., Torrent, L., Tanshi, I., Kane, A., Rutrough, A. L., Waldien, D. L., & Taylor, P. J. (2024). African bat database: Curated data of occurrences, distributions and conservation metrics for sub-Saharan bats. *Scientific Data*, 11, 1309. [https://doi.org/10.1038/s41597-024-04170-7](https://doi.org/10.1038/s41597-024-04170-7).

Monadjem, A. et al. (2024). *African Bat Database*, Figshare dataset. [https://doi.org/10.6084/m9.figshare.26363308.v1](https://doi.org/10.6084/m9.figshare.26363308.v1). The source dataset is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
