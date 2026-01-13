#!/usr/bin/env python3
"""
Explore Philadelphia's CARTO API to understand available permit fields.
"""

import requests
import json
from datetime import datetime, timedelta

# CARTO API endpoint
API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def explore_permits_fields():
    """Fetch a small sample of permits to see available fields."""
    print("Exploring permits table fields...")
    sql = "SELECT * FROM permits LIMIT 5"
    result = query_carto(sql)

    if result['rows']:
        print(f"\nFound {len(result['rows'])} sample records")
        print("\nAvailable fields:")
        for field in result['rows'][0].keys():
            print(f"  - {field}")

        print("\n\nSample record:")
        print(json.dumps(result['rows'][0], indent=2))
    return result

def explore_recent_residential_permits():
    """Look at recent residential permits to understand the data."""
    print("\n" + "="*80)
    print("Exploring recent residential permits...")

    # Get permits from the last 7 days
    sql = """
    SELECT *
    FROM permits
    WHERE permitissuedate >= (CURRENT_DATE - INTERVAL '7 days')
    LIMIT 20
    """

    result = query_carto(sql)
    print(f"Found {result.get('total_rows', len(result['rows']))} permits in last 7 days")

    if result['rows']:
        print("\nSample records:")
        for i, row in enumerate(result['rows'][:3], 1):
            print(f"\n--- Record {i} ---")
            for key, value in row.items():
                if value and key not in ['the_geom', 'the_geom_webmercator']:
                    print(f"{key}: {value}")

def explore_appeals_fields():
    """Fetch a small sample of appeals to see available fields."""
    print("\n" + "="*80)
    print("Exploring appeals table fields...")

    sql = "SELECT * FROM appeals LIMIT 5"
    try:
        result = query_carto(sql)

        if result['rows']:
            print(f"\nFound {len(result['rows'])} sample records")
            print("\nAvailable fields:")
            for field in result['rows'][0].keys():
                print(f"  - {field}")

            print("\n\nSample appeal record:")
            print(json.dumps(result['rows'][0], indent=2))
    except Exception as e:
        print(f"Error querying appeals: {e}")

if __name__ == "__main__":
    try:
        # Explore permits
        explore_permits_fields()
        explore_recent_residential_permits()

        # Explore appeals
        explore_appeals_fields()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
