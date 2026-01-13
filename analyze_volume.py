#!/usr/bin/env python3
"""
Analyze typical weekly permit volume at different unit thresholds.
This helps determine the right threshold for the weekly digest.
"""

import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict

API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def analyze_weekly_volume():
    """Analyze permit volume at different unit thresholds over recent weeks."""

    print("ANALYZING WEEKLY PERMIT VOLUME BY UNIT THRESHOLD")
    print("=" * 80)

    # Analyze last 4 weeks to get a sense of typical volume
    weeks_to_analyze = 4

    for week_offset in range(weeks_to_analyze):
        start_days_ago = (week_offset + 1) * 7
        end_days_ago = week_offset * 7

        print(f"\n\nWEEK {week_offset + 1}: {start_days_ago} to {end_days_ago} days ago")
        print("-" * 80)

        # Query for different unit thresholds
        thresholds = [3, 4, 5, 10, 20]

        for threshold in thresholds:
            sql = f"""
            SELECT COUNT(*) as count
            FROM permits
            WHERE commercialorresidential = 'Residential'
            AND numberofunits >= {threshold}
            AND permitissuedate >= (CURRENT_DATE - INTERVAL '{start_days_ago} days')
            AND permitissuedate < (CURRENT_DATE - INTERVAL '{end_days_ago} days')
            """

            result = query_carto(sql)
            count = result['rows'][0]['count'] if result['rows'] else 0
            print(f"  {threshold}+ units: {count:3d} permits")

def analyze_by_district():
    """Analyze permits by council district for last week."""

    print("\n\n" + "=" * 80)
    print("LAST WEEK'S PERMITS (5+ UNITS) BY COUNCIL DISTRICT")
    print("=" * 80)

    sql = """
    SELECT
        council_district,
        COUNT(*) as count,
        SUM(CAST(numberofunits AS INTEGER)) as total_units
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND numberofunits >= 5
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '7 days')
    GROUP BY council_district
    ORDER BY count DESC
    """

    result = query_carto(sql)

    if result['rows']:
        print("\nDistrict | Permits | Total Units")
        print("-" * 40)
        for row in result['rows']:
            district = row['council_district'] or 'Unknown'
            count = row['count']
            total_units = row['total_units'] or 0
            print(f"{district:8s} | {count:7d} | {total_units:11.0f}")
    else:
        print("No permits found in the last week")

def show_sample_permits():
    """Show sample permits from last week to understand what we're capturing."""

    print("\n\n" + "=" * 80)
    print("SAMPLE PERMITS FROM LAST WEEK (5+ UNITS)")
    print("=" * 80)

    sql = """
    SELECT
        permitnumber,
        address,
        numberofunits,
        council_district,
        permittype,
        contractorname,
        approvedscopeofwork,
        permitissuedate
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND numberofunits >= 5
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '7 days')
    ORDER BY numberofunits DESC
    LIMIT 10
    """

    result = query_carto(sql)

    if result['rows']:
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']} (District {row['council_district']})")
            print(f"   Permit: {row['permitnumber']} | {row['permittype']}")
            print(f"   Units: {row['numberofunits']} | Developer: {row.get('contractorname', 'N/A')}")
            if row.get('approvedscopeofwork'):
                # Truncate long descriptions
                scope = row['approvedscopeofwork'][:200].replace('\n', ' ').replace('\r', '')
                print(f"   Scope: {scope}...")
            print(f"   Issued: {row['permitissuedate'][:10]}")
    else:
        print("No permits found in the last week")

def analyze_appeals():
    """Analyze recent zoning appeals/variances."""

    print("\n\n" + "=" * 80)
    print("RECENT ZONING APPEALS (LAST 7 DAYS)")
    print("=" * 80)

    sql = """
    SELECT COUNT(*) as count
    FROM appeals
    WHERE createddate >= (CURRENT_DATE - INTERVAL '7 days')
    """

    result = query_carto(sql)
    count = result['rows'][0]['count'] if result['rows'] else 0
    print(f"\nTotal appeals created in last 7 days: {count}")

    # Get sample appeals
    sql = """
    SELECT
        appealnumber,
        address,
        council_district,
        appealtype,
        applicationtype,
        appealgrounds,
        createddate
    FROM appeals
    WHERE createddate >= (CURRENT_DATE - INTERVAL '30 days')
    ORDER BY createddate DESC
    LIMIT 5
    """

    result = query_carto(sql)

    if result['rows']:
        print("\nSample recent appeals (last 30 days):")
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']} (District {row.get('council_district', 'N/A')})")
            print(f"   Appeal: {row['appealnumber']} | Type: {row.get('appealtype', 'N/A')}")
            if row.get('appealgrounds'):
                # Truncate long descriptions
                grounds = row['appealgrounds'][:200].replace('\n', ' ').replace('\r', '')
                print(f"   Grounds: {grounds}...")
            print(f"   Created: {row['createddate'][:10]}")
    else:
        print("No recent appeals found")

if __name__ == "__main__":
    try:
        analyze_weekly_volume()
        analyze_by_district()
        show_sample_permits()
        analyze_appeals()

        print("\n\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("""
Based on the analysis above, consider:

1. If you want 5-15 permits per week: Use 5+ units threshold
2. If you want more comprehensive coverage: Use 3+ units threshold
3. If you want only major developments: Use 10+ units threshold

The 5+ unit threshold typically captures significant new housing construction
while filtering out smaller renovations and conversions.
        """)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
