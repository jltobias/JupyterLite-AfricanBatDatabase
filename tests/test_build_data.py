import unittest
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyproj import Geod
from shapely.geometry import Point

from scripts.build_data import (
    BANDS,
    RADIUS_KM,
    _band,
    _bat_features,
    _is_valid_coordinate,
    _jgis_project,
    _mine_buffer_features,
    _story_pages,
)


class CoordinateTests(unittest.TestCase):
    def test_accepts_valid_extreme_coordinates(self):
        self.assertTrue(_is_valid_coordinate(-180, -90))
        self.assertTrue(_is_valid_coordinate(180, 90))

    def test_rejects_sentinel_and_non_finite_coordinates(self):
        self.assertFalse(_is_valid_coordinate(-1.7976931348623157e308, 0))
        self.assertFalse(_is_valid_coordinate(float("nan"), 0))
        self.assertFalse(_is_valid_coordinate(0, float("inf")))
        self.assertFalse(_is_valid_coordinate(181, 0))


class DistanceBandTests(unittest.TestCase):
    def test_exact_thresholds_stay_in_the_inner_band(self):
        self.assertEqual(_band(1), "0-1 km")
        self.assertEqual(_band(5), ">1-5 km")
        self.assertEqual(_band(10), ">5-10 km")
        self.assertEqual(_band(50), ">40-50 km")

    def test_distances_above_study_limit_are_rejected(self):
        with self.assertRaises(ValueError):
            _band(50.001)


class SpatialBuildTests(unittest.TestCase):
    def test_jgis_project_includes_toggleable_geodesic_mine_distance_bands(self):
        page = {
            "coordinates": [0.0, 0.0],
            "facility": {
                "source_position": 12,
                "name": "Test mine",
                "country": "Test country",
                "facility_type": "mine",
                "commodity": "iron",
                "status": "active",
            },
            "band_counts": {band: index for index, band in enumerate(BANDS)},
            "nearby_record_count": 1,
            "nearest_record_km": 0.5,
        }

        buffers = _mine_buffer_features([page])
        project = _jgis_project([page])

        self.assertEqual(set(buffers), set(RADIUS_KM))
        for radius in RADIUS_KM:
            feature = buffers[radius][0]
            rings = feature["geometry"]["coordinates"]
            self.assertEqual(len(rings), 1 if radius == 1 else 2)
            self.assertEqual(rings[0][0], rings[0][-1])
            self.assertAlmostEqual(
                Geod(ellps="WGS84").inv(0.0, 0.0, *rings[0][0])[2],
                radius * 1000,
                delta=1e-6,
            )
            source = next(
                source
                for source in project["sources"].values()
                if source["parameters"].get("path") == f"data/mine_buffers_{radius}km.geojson"
            )
            layer = next(
                layer
                for layer in project["layers"].values()
                if layer["parameters"].get("source") in project["sources"]
                and project["sources"][layer["parameters"].get("source")] is source
            )
            self.assertFalse(layer["visible"])

    def test_shapefile_coordinate_precision_is_preserved(self):
        longitude = 17.123456789012345
        latitude = -3.987654321098765
        rows = gpd.GeoDataFrame(
            {
                "Family": ["Vespertilionidae"],
                "Genus": ["Myotis"],
                "Species": ["punicus"],
                "Country": ["Algeria"],
                "Location": ["Test locality"],
                "Reference": ["Example source"],
            },
            geometry=[Point(longitude, latitude)],
            crs="EPSG:4326",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "AfricanBatDatabasePoints.shp"
            rows.to_file(source, driver="ESRI Shapefile", index=False)
            archive_path = root / "points.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in root.glob("AfricanBatDatabasePoints.*"):
                    archive.write(path, path.name)

            features, invalid_count = _bat_features(archive_path, {})

        self.assertEqual(invalid_count, 0)
        self.assertEqual(features[0]["geometry"]["coordinates"], [longitude, latitude])

    def test_story_page_uses_geodesic_distance_and_source_record_id(self):
        geod = Geod(ellps="WGS84")
        longitude, latitude, _ = geod.fwd(0, 0, 90, 1000)
        points = [
            {
                "type": "Feature",
                "id": 87,
                "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "properties": {
                    "record_id": 87,
                    "scientific_name": "Myotis punicus",
                    "location": "Test locality",
                    "country": "Test country",
                },
            }
        ]
        facilities = pd.DataFrame(
            [
                {
                    "Position": 12,
                    "Country": "Test country",
                    "Location And Facility Name": "Test mine",
                    "Facility Type": "mine",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "Commodity": "iron",
                    "Mining Method": "open pit",
                    "Main Operating Company": "Example operator",
                    "Status": "active",
                    "Capacity": 10,
                    "Units": "t / yr",
                }
            ]
        )

        pages, _, nearby = _story_pages(facilities, points)

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["bat_records"][0]["record_id"], 87)
        self.assertEqual(pages[0]["bat_records"][0]["distance_band"], "0-1 km")
        self.assertEqual(nearby[0]["id"], 87)


if __name__ == "__main__":
    unittest.main()
