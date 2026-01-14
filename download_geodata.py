#!/usr/bin/env python3
"""
Download and cache Philadelphia neighborhood and council district boundaries.
"""

import requests
import json
from pathlib import Path

# GitHub repo with neighborhood boundaries
NEIGHBORHOODS_URL = "https://raw.githubusercontent.com/opendataphilly/open-geo-data/master/philadelphia-neighborhoods/philadelphia-neighborhoods.geojson"

# Council districts from Philly's CARTO
COUNCIL_DISTRICTS_URL = "https://phl.carto.com/api/v2/sql?q=SELECT%20*%20FROM%20council_districts_2024&format=geojson"

DATA_DIR = Path(__file__).parent / "geodata"

def download_neighborhoods():
    """Download Philadelphia neighborhood boundaries."""
    print("Downloading neighborhood boundaries...")

    response = requests.get(NEIGHBORHOODS_URL)
    response.raise_for_status()

    neighborhoods = response.json()

    # Save to file
    DATA_DIR.mkdir(exist_ok=True)
    output_file = DATA_DIR / "neighborhoods.geojson"

    with open(output_file, 'w') as f:
        json.dump(neighborhoods, f, indent=2)

    # Count neighborhoods
    count = len(neighborhoods.get('features', []))
    print(f"✓ Downloaded {count} neighborhoods")
    print(f"✓ Saved to {output_file}")

    # Show sample neighborhood names
    if neighborhoods.get('features'):
        names = [f['properties'].get('name', 'Unknown')
                for f in neighborhoods['features'][:10]]
        print(f"\nSample neighborhoods: {', '.join(names)}...")

    return neighborhoods

def download_council_districts():
    """Download Philadelphia council district boundaries."""
    print("\nDownloading council district boundaries...")

    try:
        response = requests.get(COUNCIL_DISTRICTS_URL)
        response.raise_for_status()

        districts = response.json()

        # Save to file
        DATA_DIR.mkdir(exist_ok=True)
        output_file = DATA_DIR / "council_districts.geojson"

        with open(output_file, 'w') as f:
            json.dump(districts, f, indent=2)

        count = len(districts.get('features', []))
        print(f"✓ Downloaded {count} council districts")
        print(f"✓ Saved to {output_file}")

        return districts
    except Exception as e:
        print(f"⚠ Could not download council districts from CARTO: {e}")
        print("  Will use council_district field from permit data instead")
        return None

def get_available_neighborhoods():
    """Get list of all available neighborhoods."""
    neighborhoods_file = DATA_DIR / "neighborhoods.geojson"

    if not neighborhoods_file.exists():
        print("Neighborhoods file not found. Downloading...")
        download_neighborhoods()

    with open(neighborhoods_file) as f:
        data = json.load(f)

    names = sorted([
        f['properties'].get('name', 'Unknown')
        for f in data.get('features', [])
    ])

    return names

def get_available_council_districts():
    """Get list of all council districts."""
    # Council districts are 1-10
    return [str(i) for i in range(1, 11)]

if __name__ == "__main__":
    print("Philadelphia Geographic Data Download")
    print("=" * 80)

    # Download both datasets
    neighborhoods = download_neighborhoods()
    districts = download_council_districts()

    print("\n" + "=" * 80)
    print("AVAILABLE GEOGRAPHIC FILTERS")
    print("=" * 80)

    # Show available neighborhoods
    names = get_available_neighborhoods()
    print(f"\n✓ {len(names)} neighborhoods available")
    print("\nSample neighborhoods:")
    for name in names[:20]:
        print(f"  - {name}")
    if len(names) > 20:
        print(f"  ... and {len(names) - 20} more")

    # Show council districts
    districts_list = get_available_council_districts()
    print(f"\n✓ {len(districts_list)} council districts available")
    print(f"  Districts: {', '.join(districts_list)}")

    print("\n✓ Setup complete! Geographic data ready for filtering.")
