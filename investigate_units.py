#!/usr/bin/env python3
"""
Investigate the numberofunits field to understand data quality.
"""

import requests
import json

API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def investigate_units_field():
    """Check how many permits have numberofunits populated."""

    print("INVESTIGATING numberofunits FIELD")
    print("=" * 80)

    # Check recent residential permits
    sql = """
    SELECT COUNT(*) as total
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '30 days')
    """
    result = query_carto(sql)
    total = result['rows'][0]['total'] if result['rows'] else 0
    print(f"\nTotal residential permits in last 30 days: {total}")

    # Check how many have numberofunits filled
    sql = """
    SELECT COUNT(*) as count
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '30 days')
    AND numberofunits IS NOT NULL
    """
    result = query_carto(sql)
    with_units = result['rows'][0]['count'] if result['rows'] else 0
    print(f"Permits with numberofunits field populated: {with_units}")

    # Check different permit types
    sql = """
    SELECT
        permittype,
        COUNT(*) as total,
        COUNT(CASE WHEN numberofunits IS NOT NULL THEN 1 END) as with_units
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '90 days')
    GROUP BY permittype
    ORDER BY total DESC
    """

    print("\n\nPERMIT TYPES (Last 90 days):")
    print("-" * 80)
    print(f"{'Permit Type':<30} {'Total':>8} {'With Units':>12}")
    print("-" * 80)

    result = query_carto(sql)
    for row in result['rows']:
        print(f"{row['permittype']:<30} {row['total']:>8} {row['with_units']:>12}")

    # Look at what fields might indicate multi-unit construction
    print("\n\n" + "=" * 80)
    print("ALTERNATIVE INDICATORS OF MULTI-UNIT CONSTRUCTION")
    print("=" * 80)

    # Check permit descriptions that might indicate multi-unit
    sql = """
    SELECT
        permitnumber,
        address,
        permittype,
        permitdescription,
        typeofwork,
        numberofunits,
        approvedscopeofwork
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '30 days')
    AND (
        LOWER(permitdescription) LIKE '%unit%'
        OR LOWER(approvedscopeofwork) LIKE '%unit%'
        OR LOWER(approvedscopeofwork) LIKE '%apartment%'
        OR LOWER(approvedscopeofwork) LIKE '%dwelling%'
        OR permittype = 'Zoning Permit'
    )
    ORDER BY permitissuedate DESC
    LIMIT 10
    """

    result = query_carto(sql)

    if result['rows']:
        print("\nSample permits that might be multi-unit:")
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']}")
            print(f"   {row['permittype']} - {row['permitdescription']}")
            print(f"   Number of units: {row.get('numberofunits', 'N/A')}")
            if row.get('approvedscopeofwork'):
                scope = row['approvedscopeofwork'][:300].replace('\n', ' ').replace('\r', ' ')
                print(f"   Scope: {scope}...")

    # Check zoning permits specifically (these often have unit counts in description)
    print("\n\n" + "=" * 80)
    print("ZONING PERMITS (Last 30 days) - Often indicate new multi-unit construction")
    print("=" * 80)

    sql = """
    SELECT
        permitnumber,
        address,
        council_district,
        numberofunits,
        approvedscopeofwork,
        permitissuedate
    FROM permits
    WHERE permittype = 'Zoning Permit'
    AND commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '30 days')
    ORDER BY permitissuedate DESC
    LIMIT 15
    """

    result = query_carto(sql)

    if result['rows']:
        print(f"\nFound {len(result['rows'])} zoning permits:")
        for i, row in enumerate(result['rows'], 1):
            print(f"\n{i}. {row['address']} (District {row.get('council_district', 'N/A')})")
            print(f"   Permit: {row['permitnumber']} | Units: {row.get('numberofunits', 'N/A')}")
            if row.get('approvedscopeofwork'):
                scope = row['approvedscopeofwork'][:250].replace('\n', ' ').replace('\r', ' ')
                print(f"   {scope}...")
            print(f"   Issued: {row['permitissuedate'][:10]}")
    else:
        print("No zoning permits found in last 30 days")

if __name__ == "__main__":
    try:
        investigate_units_field()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
