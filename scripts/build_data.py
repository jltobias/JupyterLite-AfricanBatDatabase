from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from pyproj import Geod, Transformer


ROOT = Path(__file__).resolve().parents[1]
BAT_SHAPEFILE = ROOT / "data" / "source" / "AfricanBatDatabasePoints.zip"
SPECIES_PROFILES = ROOT / "data" / "species_profiles.json"
PHOTO_DIR = ROOT / "assets" / "photos"
USGS_URL = "https://pubs.usgs.gov/of/2006/1135/table1.xls"
RADIUS_KM = (1, 5, 10, 20, 30, 40, 50)
BANDS = ("0-1 km", ">1-5 km", ">5-10 km", ">10-20 km", ">20-30 km", ">30-40 km", ">40-50 km")
MAX_DISTANCE_M = 50_000
GEOD = Geod(ellps="WGS84")
WEB_MERCATOR = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


class DataBuildError(RuntimeError):
    pass


def _safe_extract_shapefile(archive_path: Path, destination: Path) -> Path:
    required = {
        "AfricanBatDatabasePoints.shp",
        "AfricanBatDatabasePoints.shx",
        "AfricanBatDatabasePoints.dbf",
        "AfricanBatDatabasePoints.prj",
    }
    with zipfile.ZipFile(archive_path) as archive:
        names = {Path(item.filename).name for item in archive.infolist()}
        unsafe = [
            item.filename
            for item in archive.infolist()
            if Path(item.filename).is_absolute() or ".." in Path(item.filename).parts
        ]
        if unsafe:
            raise DataBuildError("The bat shapefile archive contains unsafe paths.")
        if not required.issubset(names):
            raise DataBuildError("The bat shapefile archive is missing required files.")
        for item in archive.infolist():
            name = Path(item.filename).name
            if name in required or name == "AfricanBatDatabasePoints.cpg":
                (destination / name).write_bytes(archive.read(item))
    return destination / "AfricanBatDatabasePoints.shp"


def _is_valid_coordinate(longitude: Any, latitude: Any) -> bool:
    try:
        longitude = float(longitude)
        latitude = float(latitude)
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(longitude)
        and math.isfinite(latitude)
        and -180 <= longitude <= 180
        and -90 <= latitude <= 90
    )


def _value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _feature_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _bat_features(shapefile_path: Path, profiles: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    with tempfile.TemporaryDirectory(prefix="african-bat-points-") as temp_dir:
        shapefile = _safe_extract_shapefile(shapefile_path, Path(temp_dir))
        points = gpd.read_file(shapefile)

    required = {"Family", "Genus", "Species", "Country", "Location", "Reference"}
    missing = required.difference(points.columns)
    if missing:
        raise DataBuildError(f"The bat shapefile is missing fields: {', '.join(sorted(missing))}")
    if points.crs is None or points.crs.to_epsg() != 4326:
        raise DataBuildError("The bat point shapefile must use EPSG:4326.")

    features = []
    invalid_count = 0
    for row_number, row in points.iterrows():
        if row.geometry is None or row.geometry.is_empty or row.geometry.geom_type != "Point":
            invalid_count += 1
            continue
        longitude = float(row.geometry.x)
        latitude = float(row.geometry.y)
        if not _is_valid_coordinate(longitude, latitude):
            invalid_count += 1
            continue

        genus = str(row["Genus"]).strip() if pd.notna(row["Genus"]) else ""
        epithet = str(row["Species"]).strip() if pd.notna(row["Species"]) else ""
        scientific_name = " ".join(part for part in (genus, epithet) if part)
        profile = profiles.get(scientific_name, {})
        properties = {
            "record_id": int(row_number) + 1,
            "family": _value(row["Family"]),
            "genus": genus or None,
            "species": epithet or None,
            "scientific_name": scientific_name or None,
            "english_name": profile.get("english_name"),
            "name_source": profile.get("name_source"),
            "museum_number": _value(row.get("Museum_num")),
            "date": _value(row.get("Date")),
            "year": _value(row.get("Year")),
            "country": _value(row["Country"]),
            "location": _value(row["Location"]),
            "reference": _value(row["Reference"]),
            "holotype": _value(row.get("Holotype")),
            "checked": _value(row.get("Checked")),
            "diet": profile.get("diet"),
            "diet_source": profile.get("diet_source"),
            "foraging_range": profile.get("foraging_range"),
            "foraging_source": profile.get("foraging_source"),
            "disease_note": profile.get("disease_note"),
            "image": profile.get("image"),
            "image_credit": profile.get("image_credit"),
            "image_source": profile.get("image_source"),
        }
        features.append(
            {
                "type": "Feature",
                "id": properties["record_id"],
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "properties": properties,
            }
        )
    return features, invalid_count


def _facility_data(source_url: str, countries: set[str]) -> pd.DataFrame:
    response = requests.get(source_url, timeout=90)
    response.raise_for_status()
    facilities = pd.read_excel(BytesIO(response.content), engine="xlrd")
    required = {
        "Position",
        "Country",
        "Location And Facility Name",
        "Facility Type",
        "DD Latitude",
        "DD Longitude",
    }
    missing = required.difference(facilities.columns)
    if missing:
        raise DataBuildError(f"The USGS table is missing fields: {', '.join(sorted(missing))}")
    facilities["latitude"] = pd.to_numeric(facilities["DD Latitude"], errors="coerce")
    facilities["longitude"] = pd.to_numeric(facilities["DD Longitude"], errors="coerce")
    valid = facilities.apply(
        lambda row: _is_valid_coordinate(row["longitude"], row["latitude"]), axis=1
    )
    return facilities.loc[valid & facilities["Country"].isin(countries)].copy()


def _facility_feature(row: pd.Series) -> dict[str, Any]:
    properties = {
        "facility_id": f"USGS-2006-{int(row['Position'])}",
        "source_position": int(row["Position"]),
        "country": _value(row["Country"]),
        "name": _value(row["Location And Facility Name"]),
        "facility_type": _value(row["Facility Type"]),
        "commodity": _value(row["Commodity"]),
        "mining_method": _value(row["Mining Method"]),
        "operator": _value(row["Main Operating Company"]),
        "status": _value(row["Status"]),
        "capacity": _value(row["Capacity"]),
        "units": _value(row["Units"]),
    }
    return {
        "type": "Feature",
        "id": properties["facility_id"],
        "geometry": {
            "type": "Point",
            "coordinates": [float(row["longitude"]), float(row["latitude"])],
        },
        "properties": properties,
    }


def _band(distance_km: float) -> str:
    for band, radius in zip(BANDS, RADIUS_KM, strict=True):
        if distance_km <= radius:
            return band
    raise ValueError("Distance is outside the 50 km study area.")


def _story_pages(
    facilities: pd.DataFrame, bat_features: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    points = [feature["geometry"]["coordinates"] for feature in bat_features]
    point_longitudes = np.asarray([point[0] for point in points], dtype=float)
    point_latitudes = np.asarray([point[1] for point in points], dtype=float)
    facility_features = []
    pages = []
    used_records: set[int] = set()

    for _, facility in facilities.iterrows():
        facility_feature = _facility_feature(facility)
        facility_features.append(facility_feature)
        if str(facility.get("Facility Type", "")).strip().lower() != "mine":
            continue

        longitude = float(facility["longitude"])
        latitude = float(facility["latitude"])
        lat_delta = 0.51
        lon_delta = min(180.0, 0.51 / max(abs(math.cos(math.radians(latitude))), 0.01))
        candidates = np.flatnonzero(
            (np.abs(point_latitudes - latitude) <= lat_delta)
            & (np.abs(point_longitudes - longitude) <= lon_delta)
        )
        if candidates.size == 0:
            continue

        _, _, distance_m = GEOD.inv(
            np.full(candidates.size, longitude),
            np.full(candidates.size, latitude),
            point_longitudes[candidates],
            point_latitudes[candidates],
        )
        matched = []
        band_counts = dict.fromkeys(BANDS, 0)
        for candidate, meters in zip(candidates, distance_m, strict=True):
            if meters > MAX_DISTANCE_M:
                continue
            record = bat_features[int(candidate)]
            distance_km = float(meters) / 1000
            record_copy = dict(record["properties"])
            record_copy["coordinates"] = record["geometry"]["coordinates"]
            record_copy["distance_km"] = round(distance_km, 3)
            record_copy["distance_band"] = _band(distance_km)
            matched.append(record_copy)
            used_records.add(record["id"])
            band_counts[record_copy["distance_band"]] += 1

        if not matched:
            continue
        matched.sort(key=lambda item: (item["distance_km"], item["scientific_name"] or ""))
        facility_feature["properties"]["nearby_record_count"] = len(matched)
        facility_feature["properties"]["nearest_record_km"] = matched[0]["distance_km"]
        pages.append(
            {
                "facility": facility_feature["properties"],
                "coordinates": [longitude, latitude],
                "nearby_record_count": len(matched),
                "nearest_record_km": matched[0]["distance_km"],
                "band_counts": band_counts,
                "bat_records": matched,
            }
        )

    pages.sort(
        key=lambda page: (
            str(page["facility"]["country"] or ""),
            str(page["facility"]["name"] or ""),
            page["facility"]["source_position"],
        )
    )
    nearby_features = [feature for feature in bat_features if feature["id"] in used_records]
    return pages, facility_features, nearby_features


def _story_image(facility: dict[str, Any], photos: Path) -> tuple[str, str] | tuple[None, None]:
    name = str(facility.get("name") or "").lower()
    candidates = {
        "ouenza": ("ouenza-mine.jpg", "Michkar, CC BY-SA 4.0"),
        "kherzet youcef": ("kherzet-youcef-mine.jpg", "Missaad, CC BY-SA 4.0"),
    }
    for token, (filename, credit) in candidates.items():
        if token in name and (photos / filename).exists():
            return f"assets/photos/{filename}", credit
    return None, None


def _geodesic_ring(longitude: float, latitude: float, radius_km: int, *, clockwise: bool) -> list[list[float]]:
    coordinates = [
        list(GEOD.fwd(longitude, latitude, bearing, radius_km * 1000)[:2])
        for bearing in range(0, 360, 5)
    ]
    if not clockwise:
        coordinates.reverse()
    coordinates.append(coordinates[0])
    return coordinates


def _mine_buffer_features(pages: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    buffers: dict[int, list[dict[str, Any]]] = {radius: [] for radius in RADIUS_KM}
    for page in pages:
        longitude, latitude = page["coordinates"]
        facility = page["facility"]
        inner_radius_km = 0
        for index, outer_radius_km in enumerate(RADIUS_KM):
            rings = [_geodesic_ring(longitude, latitude, outer_radius_km, clockwise=False)]
            if inner_radius_km:
                rings.append(_geodesic_ring(longitude, latitude, inner_radius_km, clockwise=True))
            buffers[outer_radius_km].append(
                {
                    "type": "Feature",
                    "id": f"{facility['source_position']}-{inner_radius_km}-{outer_radius_km}",
                    "geometry": {"type": "Polygon", "coordinates": rings},
                    "properties": {
                        "facility_source_position": facility["source_position"],
                        "facility_name": facility["name"],
                        "country": facility["country"],
                        "inner_radius_km": inner_radius_km,
                        "outer_radius_km": outer_radius_km,
                        "bat_records_in_band": page["band_counts"][BANDS[index]],
                    },
                }
            )
            inner_radius_km = outer_radius_km
    return buffers


def _jgis_project(pages: list[dict[str, Any]]) -> dict[str, Any]:
    story_id = str(uuid.uuid4())
    base_source_id = str(uuid.uuid4())
    facility_source_id = str(uuid.uuid4())
    bat_source_id = str(uuid.uuid4())
    base_layer_id = str(uuid.uuid4())
    facility_layer_id = str(uuid.uuid4())
    bat_layer_id = str(uuid.uuid4())
    buffer_source_ids = {radius: str(uuid.uuid4()) for radius in RADIUS_KM}
    buffer_layer_ids = {radius: str(uuid.uuid4()) for radius in RADIUS_KM}
    segment_ids = [str(uuid.uuid4()) for _ in pages]

    layers: dict[str, Any] = {
        base_layer_id: {
            "name": "OpenStreetMap",
            "type": "RasterLayer",
            "visible": True,
            "parameters": {"opacity": 1.0, "source": base_source_id},
        },
        facility_layer_id: {
            "name": "USGS mineral facilities (2006)",
            "type": "VectorLayer",
            "visible": True,
            "parameters": {"opacity": 1.0, "source": facility_source_id, "symbologyState": {}},
        },
        bat_layer_id: {
            "name": "African Bat Database point localities",
            "type": "VectorLayer",
            "visible": True,
            "parameters": {"opacity": 1.0, "source": bat_source_id, "symbologyState": {}},
        },
    }
    for radius in RADIUS_KM:
        inner_radius_km = RADIUS_KM[RADIUS_KM.index(radius) - 1] if radius != RADIUS_KM[0] else 0
        layers[buffer_layer_ids[radius]] = {
            "name": f"Mine distance band: {inner_radius_km}-{radius} km",
            "type": "VectorLayer",
            "visible": False,
            "parameters": {
                "opacity": 0.35,
                "source": buffer_source_ids[radius],
                "symbologyState": {},
            },
        }
    for index, (page, segment_id) in enumerate(zip(pages, segment_ids, strict=True), start=1):
        facility = page["facility"]
        coords = page["coordinates"]
        x, y = WEB_MERCATOR.transform(*coords)
        extent = [x - 120_000, y - 120_000, x + 120_000, y + 120_000]
        image, credit = _story_image(facility, PHOTO_DIR)
        story_text = (
            f"### {facility['name']}, {facility['country']}\n\n"
            f"**Facility:** {facility['facility_type'] or 'not recorded'} · "
            f"**Commodity:** {facility['commodity'] or 'not recorded'} · "
            f"**Status in 2006 source:** {facility['status'] or 'not recorded'}\n\n"
            f"**Bat point records within 50 km:** {page['nearby_record_count']} · "
            f"**Nearest record:** {page['nearest_record_km']:.1f} km.\n\n"
            "These are occurrence localities, not a confirmed-roost inventory. "
            "Distances do not establish impact, habitat use, exposure, or disease risk.\n\n"
            "[Open the interactive map for selectable distance rings and species cards](../storymap/)."
        )
        layers[segment_id] = {
            "name": f"{index}. {facility['name']}",
            "type": "StorySegmentLayer",
            "visible": True,
            "parameters": {
                "content": {
                    "contentMode": "markdown",
                    "title": f"{index}. {facility['name']}",
                    "markdown": story_text,
                    "image": image or "",
                    "imageCaption": credit or "",
                    "paneAlignment": "start",
                    "panelWidth": "34%",
                },
                "extent": extent,
                "zoom": 7,
                "transition": {"type": "smooth", "time": 1},
                "layerOverride": [],
            },
        }

    if pages:
        initial = pages[0]
        lon, lat = initial["coordinates"]
        x, y = WEB_MERCATOR.transform(lon, lat)
        initial_extent = [x - 120_000, y - 120_000, x + 120_000, y + 120_000]
    else:
        lon, lat = 20.0, 0.0
        initial_extent = [-2_000_000, -4_000_000, 5_000_000, 4_000_000]

    return {
        "schemaVersion": "0.6.0",
        "metadata": {},
        "layerTree": [
            base_layer_id,
            facility_layer_id,
            bat_layer_id,
            *[buffer_layer_ids[radius] for radius in RADIUS_KM],
            *segment_ids,
        ],
        "layers": layers,
        "sources": {
            base_source_id: {
                "name": "OpenStreetMap",
                "type": "RasterSource",
                "parameters": {
                    "provider": "OpenStreetMap",
                    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                    "attribution": "(C) OpenStreetMap contributors",
                    "minZoom": 0,
                    "maxZoom": 19,
                    "interpolate": False,
                    "urlParameters": {},
                },
            },
            facility_source_id: {
                "name": "USGS facilities",
                "type": "GeoJSONSource",
                "parameters": {"path": "data/facilities.geojson", "httpHeaders": ""},
            },
            bat_source_id: {
                "name": "Bat occurrence points",
                "type": "GeoJSONSource",
                "parameters": {"path": "data/bat_points.geojson", "httpHeaders": ""},
            },
            **{
                buffer_source_ids[radius]: {
                    "name": f"Mine distance band: {radius} km",
                    "type": "GeoJSONSource",
                    "parameters": {
                        "path": f"data/mine_buffers_{radius}km.geojson",
                        "httpHeaders": "",
                    },
                }
                for radius in RADIUS_KM
            },
        },
        "stories": {
            story_id: {
                "showGradient": True,
                "storySegments": segment_ids,
                "storyType": "guided",
                "title": "African Bats & Mining",
            }
        },
        "options": {
            "bearing": 0,
            "extent": initial_extent,
            "latitude": lat,
            "longitude": lon,
            "mapAdapter": "openlayers",
            "pitch": 0,
            "projection": "EPSG:3857",
            "zoom": 7,
        },
        "viewState": {},
    }


def build(output_dir: Path, shapefile_path: Path = BAT_SHAPEFILE) -> dict[str, Any]:
    if not shapefile_path.is_file():
        raise DataBuildError(f"Bat point shapefile not found: {shapefile_path}")
    if not SPECIES_PROFILES.is_file():
        raise DataBuildError(f"Species profiles not found: {SPECIES_PROFILES}")
    profiles = json.loads(SPECIES_PROFILES.read_text(encoding="utf-8"))
    bat_features, invalid_bat_count = _bat_features(shapefile_path, profiles)
    if not bat_features:
        raise DataBuildError("No valid bat point records were found.")

    countries = {feature["properties"]["country"] for feature in bat_features}
    facilities = _facility_data(USGS_URL, countries)

    pages, facility_features, nearby_features = _story_pages(facilities, bat_features)
    lite_root = output_dir / "lite"
    out_lite = lite_root / "content"
    out_story = output_dir / "storymap"
    for destination in (out_lite / "data", out_story / "data"):
        destination.mkdir(parents=True, exist_ok=True)

    _write_json(out_lite / "data" / "facilities.geojson", _feature_collection(facility_features))
    _write_json(out_lite / "data" / "bat_points.geojson", _feature_collection(bat_features))
    _write_json(out_lite / "data" / "nearby_bat_points.geojson", _feature_collection(nearby_features))
    for radius, features in _mine_buffer_features(pages).items():
        _write_json(out_lite / "data" / f"mine_buffers_{radius}km.geojson", _feature_collection(features))
    story_data = {
        "source": {
            "bat": "Monadjem et al. (2024), African Bat Database shapefile supplied for this project; source version 1.",
            "mining": "Eros & Candelario-Quintana (2006), USGS Open-File Report 2006-1135, Table 1.",
            "bat_license": "CC BY 4.0",
            "bat_url": "https://doi.org/10.6084/m9.figshare.26363308.v1",
            "mining_url": "https://pubs.usgs.gov/of/2006/1135/",
            "crs": "EPSG:4326",
            "coordinate_precision": "Original valid shapefile coordinates retained without rounding.",
        },
        "summary": {
            "input_bat_records": len(bat_features) + invalid_bat_count,
            "valid_bat_records": len(bat_features),
            "invalid_bat_coordinates_excluded": invalid_bat_count,
            "coordinate_valid_facilities": len(facility_features),
            "mine_pages_with_bat_records_within_50km": len(pages),
            "unique_bat_records_near_mines": len(nearby_features),
            "mine_record_associations": sum(page["nearby_record_count"] for page in pages),
            "species_near_mines": len(
                {
                    record["scientific_name"]
                    for page in pages
                    for record in page["bat_records"]
                    if record["scientific_name"]
                }
            ),
        },
        "radius_km": list(RADIUS_KM),
        "pages": pages,
    }
    _write_json(out_story / "data" / "storymap.json", story_data)
    _write_json(out_lite / "data" / "storymap.json", story_data)
    _write_json(out_lite / "african_bat_mines_story.jGIS", _jgis_project(pages))

    shutil.copytree(ROOT / "book" / "notebooks", out_lite / "notebooks", dirs_exist_ok=True)
    shutil.copytree(PHOTO_DIR, out_lite / "assets" / "photos", dirs_exist_ok=True)
    shutil.copytree(PHOTO_DIR, out_story / "assets" / "photos", dirs_exist_ok=True)
    shutil.copyfile(SPECIES_PROFILES, out_story / "data" / "species_profiles.json")
    shutil.copyfile(SPECIES_PROFILES, out_lite / "data" / "species_profiles.json")
    shutil.copyfile(ROOT / "lite" / "environment.yml", lite_root / "environment.yml")
    shutil.copyfile(ROOT / "book" / "media-credits.md", out_lite / "media-credits.md")

    return story_data["summary"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build storymap data from the bat point shapefile and USGS table.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "_build" / "generated")
    parser.add_argument("--bat-shapefile", type=Path, default=BAT_SHAPEFILE)
    args = parser.parse_args()
    summary = build(args.output_dir, args.bat_shapefile)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
