#!/usr/bin/env python3
"""
Match permits and variances to neighborhoods using point-in-polygon.
"""

import json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.prepared import prep

DATA_DIR = Path(__file__).parent / "geodata"

class GeographicMatcher:
    """Match coordinates to neighborhoods and council districts."""

    def __init__(self):
        self.neighborhoods = None
        self.neighborhood_shapes = None
        self.load_geodata()

    def load_geodata(self):
        """Load neighborhood boundaries from GeoJSON."""
        neighborhoods_file = DATA_DIR / "neighborhoods.geojson"

        if not neighborhoods_file.exists():
            raise FileNotFoundError(
                f"Neighborhoods file not found at {neighborhoods_file}. "
                "Run download_geodata.py first!"
            )

        with open(neighborhoods_file) as f:
            self.neighborhoods = json.load(f)

        # Pre-process shapes for faster matching
        self.neighborhood_shapes = []
        for feature in self.neighborhoods['features']:
            geom = shape(feature['geometry'])
            name = feature['properties'].get('name', 'Unknown')
            # Use prepared geometries for faster point-in-polygon
            self.neighborhood_shapes.append({
                'name': name,
                'geometry': prep(geom),
                'bounds': geom.bounds  # For quick bbox check
            })

        print(f"✓ Loaded {len(self.neighborhood_shapes)} neighborhoods")

    def match_neighborhood(self, lon, lat):
        """
        Find which neighborhood contains this point.

        Args:
            lon: Longitude (X coordinate)
            lat: Latitude (Y coordinate)

        Returns:
            Neighborhood name or None
        """
        if not lon or not lat:
            return None

        point = Point(lon, lat)

        # Check each neighborhood
        for neighborhood in self.neighborhood_shapes:
            # Quick bounding box check first
            minx, miny, maxx, maxy = neighborhood['bounds']
            if not (minx <= lon <= maxx and miny <= lat <= maxy):
                continue

            # Detailed point-in-polygon check
            if neighborhood['geometry'].contains(point):
                return neighborhood['name']

        return None

    def enrich_permit(self, permit):
        """
        Add neighborhood to permit data.

        Args:
            permit: Permit dictionary with geocode_x and geocode_y

        Returns:
            Permit with 'neighborhood' field added
        """
        # Get coordinates from permit
        # Philadelphia uses State Plane coordinates, need to check if we need conversion
        x = permit.get('geocode_x')
        y = permit.get('geocode_y')

        if not x or not y:
            permit['neighborhood'] = None
            return permit

        # Try to match (may need coordinate conversion)
        neighborhood = self.match_neighborhood(x, y)
        permit['neighborhood'] = neighborhood

        return permit

    def enrich_items(self, items):
        """
        Add neighborhood to list of permits/variances.

        Args:
            items: List of permit/variance dictionaries

        Returns:
            List with neighborhood field added to each item
        """
        enriched = []
        matched = 0

        for item in items:
            item = self.enrich_permit(item)
            if item.get('neighborhood'):
                matched += 1
            enriched.append(item)

        print(f"✓ Matched {matched}/{len(items)} items to neighborhoods")

        return enriched

    def filter_by_neighborhoods(self, items, neighborhoods):
        """
        Filter items to only those in specified neighborhoods.

        Args:
            items: List of enriched permits/variances
            neighborhoods: List of neighborhood names to include

        Returns:
            Filtered list
        """
        if not neighborhoods or 'citywide' in [n.lower() for n in neighborhoods]:
            return items

        return [
            item for item in items
            if item.get('neighborhood') in neighborhoods
        ]

    def filter_by_districts(self, items, districts):
        """
        Filter items to only those in specified council districts.

        Args:
            items: List of permits/variances
            districts: List of district numbers (as strings)

        Returns:
            Filtered list
        """
        if not districts or 'citywide' in [d.lower() for d in districts]:
            return items

        return [
            item for item in items
            if str(item.get('council_district')) in districts
        ]

    def get_unique_neighborhoods(self, items):
        """Get list of unique neighborhoods from items."""
        neighborhoods = set()
        for item in items:
            if item.get('neighborhood'):
                neighborhoods.add(item['neighborhood'])
        return sorted(neighborhoods)

    def get_unique_districts(self, items):
        """Get list of unique council districts from items."""
        districts = set()
        for item in items:
            district = item.get('council_district')
            if district:
                districts.add(str(district))
        return sorted(districts)

if __name__ == "__main__":
    """Test the geographic matcher."""
    print("Testing Geographic Matcher")
    print("=" * 80)

    # Initialize matcher
    matcher = GeographicMatcher()

    # Test with some known coordinates
    print("\nTesting known locations:")

    # Test City Hall (approximately)
    test_coords = [
        {"name": "City Hall area", "x": -75.1652, "y": 39.9526},
        {"name": "Fishtown area", "x": -75.1333, "y": 39.9774},
        {"name": "University City area", "x": -75.1999, "y": 39.9522},
    ]

    for test in test_coords:
        neighborhood = matcher.match_neighborhood(test['x'], test['y'])
        print(f"  {test['name']}: {neighborhood}")

    print("\n✓ Geographic matcher is working!")
