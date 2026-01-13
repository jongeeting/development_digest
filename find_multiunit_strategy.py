#!/usr/bin/env python3
"""
Find a better strategy for identifying multi-unit construction permits.
Since numberofunits is rarely populated, we need to use other indicators.
"""

import requests
import re

API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def check_new_construction_permits():
    """Look for permits that indicate new construction."""

    print("NEW CONSTRUCTION PERMITS (Last 30 days)")
    print("=" * 80)

    sql = """
    SELECT
        permitnumber,
        address,
        council_district,
        permittype,
        typeofwork,
        numberofunits,
        approvedscopeofwork,
        permitissuedate
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '30 days')
    AND typeofwork = 'New Construction'
    AND permittype IN ('Residential Building', 'Zoning', 'Zoning Permit')
    ORDER BY permitissuedate DESC
    LIMIT 20
    """

    result = query_carto(sql)

    if result['rows']:
        print(f"\nFound {len(result['rows'])} new construction permits:")
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']} (District {row.get('council_district', 'N/A')})")
            print(f"   {row['permitnumber']} | {row['permittype']} | {row['typeofwork']}")
            print(f"   Units: {row.get('numberofunits', 'N/A')}")

            # Try to extract unit count from scope
            if row.get('approvedscopeofwork'):
                scope = row['approvedscopeofwork']
                print(f"   Scope: {scope[:200]}...")

                # Look for unit mentions
                unit_patterns = [
                    r'(\d+)[\s-]*unit',
                    r'(\d+)[\s-]*dwelling',
                    r'(\d+)[\s-]*family',
                ]
                for pattern in unit_patterns:
                    matches = re.findall(pattern, scope.lower())
                    if matches:
                        print(f"   >>> Possible unit count: {matches}")
                        break
    else:
        print("No new construction permits found")

def check_permits_with_units_populated():
    """Look at permits where numberofunits is actually populated."""

    print("\n\n" + "=" * 80)
    print("PERMITS WITH NUMBEROFUNITS POPULATED (Last 60 days)")
    print("=" * 80)

    sql = """
    SELECT
        permitnumber,
        address,
        council_district,
        permittype,
        typeofwork,
        numberofunits,
        approvedscopeofwork,
        permitissuedate
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND numberofunits IS NOT NULL
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '60 days')
    ORDER BY permitissuedate DESC
    LIMIT 25
    """

    result = query_carto(sql)

    if result['rows']:
        print(f"\nFound {len(result['rows'])} permits with unit counts:")
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']} (District {row.get('council_district', 'N/A')})")
            print(f"   {row['permitnumber']} | {row['permittype']} | Units: {row.get('numberofunits')}")
            print(f"   Type of work: {row.get('typeofwork', 'N/A')}")
            print(f"   Issued: {row['permitissuedate'][:10]}")
            if row.get('approvedscopeofwork'):
                scope = row['approvedscopeofwork'][:250].replace('\n', ' ').replace('\r', ' ')
                print(f"   {scope}...")

def check_keywords_for_multiunit():
    """Search for keywords that might indicate multi-unit development."""

    print("\n\n" + "=" * 80)
    print("POTENTIAL MULTI-UNIT PERMITS (Keyword search, last 14 days)")
    print("=" * 80)

    # Keywords that might indicate multi-unit
    keywords = [
        "apartment",
        "multi-family",
        "multifamily",
        "townhouse",
        "row home",
        "dwelling units"
    ]

    sql = f"""
    SELECT
        permitnumber,
        address,
        council_district,
        permittype,
        typeofwork,
        numberofunits,
        approvedscopeofwork,
        permitissuedate
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '14 days')
    AND (
        LOWER(approvedscopeofwork) LIKE '%apartment%'
        OR LOWER(approvedscopeofwork) LIKE '%multi-family%'
        OR LOWER(approvedscopeofwork) LIKE '%multifamily%'
        OR LOWER(approvedscopeofwork) LIKE '%townhouse%'
        OR LOWER(approvedscopeofwork) LIKE '% units %'
        OR LOWER(approvedscopeofwork) LIKE '%dwelling units%'
    )
    ORDER BY permitissuedate DESC
    LIMIT 15
    """

    result = query_carto(sql)

    if result['rows']:
        print(f"\nFound {len(result['rows'])} potential multi-unit permits:")
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']} (District {row.get('council_district', 'N/A')})")
            print(f"   {row['permitnumber']} | {row['permittype']}")
            print(f"   Units field: {row.get('numberofunits', 'N/A')}")

            if row.get('approvedscopeofwork'):
                scope = row['approvedscopeofwork'][:300].replace('\n', ' ').replace('\r', ' ')
                print(f"   {scope}...")

if __name__ == "__main__":
    try:
        check_new_construction_permits()
        check_permits_with_units_populated()
        check_keywords_for_multiunit()

        print("\n\n" + "=" * 80)
        print("STRATEGY RECOMMENDATION")
        print("=" * 80)
        print("""
Given the data quality issues with numberofunits:

OPTION 1: Focus on permits with numberofunits populated (most reliable)
  - Pro: Clean data with actual unit counts
  - Con: Misses most permits (only 3% have this field filled)

OPTION 2: Use permit type + keywords in scope of work
  - Pro: Catches more developments
  - Con: Requires text parsing and may miss some

OPTION 3: Hybrid approach
  - Start with numberofunits when available
  - Supplement with keyword search in scope of work
  - Focus on specific permit types (Residential Building, Zoning)

RECOMMENDATION: Use Option 3 - Hybrid approach
This gives you the most comprehensive coverage while maintaining quality.
        """)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
