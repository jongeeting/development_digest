#!/usr/bin/env python3
"""
Analyze daily permit and variance volumes to inform newsletter strategy.
"""

import requests
from datetime import datetime, timedelta
from collections import defaultdict

API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def analyze_daily_volume():
    """Analyze daily permit and variance volumes over the past 30 days."""

    print("DAILY VOLUME ANALYSIS (Last 30 Days)")
    print("=" * 80)

    # Get permits by day
    sql = """
    SELECT
        DATE(permitissuedate) as issue_date,
        COUNT(*) as count,
        STRING_AGG(DISTINCT council_district, ', ' ORDER BY council_district) as districts
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '30 days')
    AND typeofwork = 'New Construction'
    GROUP BY DATE(permitissuedate)
    ORDER BY issue_date DESC
    """

    result = query_carto(sql)
    permits_by_day = result.get('rows', [])

    # Get appeals by day
    sql = """
    SELECT
        DATE(createddate) as created_date,
        COUNT(*) as count,
        STRING_AGG(DISTINCT council_district, ', ' ORDER BY council_district) as districts
    FROM appeals
    WHERE createddate >= (CURRENT_DATE - INTERVAL '30 days')
    AND (
        applicationtype LIKE '%ZBA%'
        OR appealtype LIKE '%Variance%'
        OR LOWER(appealgrounds) LIKE '%variance%'
    )
    GROUP BY DATE(createddate)
    ORDER BY created_date DESC
    """

    result = query_carto(sql)
    appeals_by_day = result.get('rows', [])

    print("\nPERMITS BY DAY:")
    print("-" * 80)
    print(f"{'Date':<15} {'Count':<8} {'Districts'}")
    print("-" * 80)

    permit_counts = []
    for row in permits_by_day[:30]:
        date = row['issue_date'][:10] if row['issue_date'] else 'Unknown'
        count = row['count']
        districts = row.get('districts', 'N/A')
        permit_counts.append(count)
        print(f"{date:<15} {count:<8} {districts}")

    print("\nVARIANCES BY DAY:")
    print("-" * 80)
    print(f"{'Date':<15} {'Count':<8} {'Districts'}")
    print("-" * 80)

    variance_counts = []
    for row in appeals_by_day[:30]:
        date = row['created_date'][:10] if row['created_date'] else 'Unknown'
        count = row['count']
        districts = row.get('districts', 'N/A')
        variance_counts.append(count)
        print(f"{date:<15} {count:<8} {districts}")

    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)

    if permit_counts:
        print(f"\nPERMITS (last {len(permit_counts)} days with activity):")
        print(f"  Average per day: {sum(permit_counts)/len(permit_counts):.1f}")
        print(f"  Min: {min(permit_counts)}")
        print(f"  Max: {max(permit_counts)}")
        print(f"  Total: {sum(permit_counts)}")

        # Calculate days with 0, 1, 2, 3+ permits
        days_with_0 = 30 - len(permit_counts)
        days_with_1 = sum(1 for c in permit_counts if c == 1)
        days_with_2 = sum(1 for c in permit_counts if c == 2)
        days_with_3_plus = sum(1 for c in permit_counts if c >= 3)

        print(f"\n  Distribution:")
        print(f"    Days with 0 permits: {days_with_0}")
        print(f"    Days with 1 permit:  {days_with_1}")
        print(f"    Days with 2 permits: {days_with_2}")
        print(f"    Days with 3+ permits: {days_with_3_plus}")

    if variance_counts:
        print(f"\nVARIANCES (last {len(variance_counts)} days with activity):")
        print(f"  Average per day: {sum(variance_counts)/len(variance_counts):.1f}")
        print(f"  Min: {min(variance_counts)}")
        print(f"  Max: {max(variance_counts)}")
        print(f"  Total: {sum(variance_counts)}")

        # Calculate distribution
        days_with_0 = 30 - len(variance_counts)
        days_with_1 = sum(1 for c in variance_counts if c == 1)
        days_with_2 = sum(1 for c in variance_counts if c == 2)
        days_with_3_plus = sum(1 for c in variance_counts if c >= 3)

        print(f"\n  Distribution:")
        print(f"    Days with 0 variances: {days_with_0}")
        print(f"    Days with 1 variance:  {days_with_1}")
        print(f"    Days with 2 variances: {days_with_2}")
        print(f"    Days with 3+ variances: {days_with_3_plus}")

    # Combined daily totals
    print("\n" + "=" * 80)
    print("COMBINED DAILY ACTIVITY")
    print("=" * 80)

    # Merge by date
    all_dates = set()
    permit_dict = {row['issue_date'][:10]: row['count'] for row in permits_by_day if row.get('issue_date')}
    variance_dict = {row['created_date'][:10]: row['count'] for row in appeals_by_day if row.get('created_date')}
    all_dates.update(permit_dict.keys())
    all_dates.update(variance_dict.keys())

    combined = []
    for date in sorted(all_dates, reverse=True):
        permits = permit_dict.get(date, 0)
        variances = variance_dict.get(date, 0)
        total = permits + variances
        combined.append({'date': date, 'permits': permits, 'variances': variances, 'total': total})

    print(f"\n{'Date':<15} {'Permits':<10} {'Variances':<12} {'Total'}")
    print("-" * 80)
    for item in combined[:30]:
        print(f"{item['date']:<15} {item['permits']:<10} {item['variances']:<12} {item['total']}")

    totals = [item['total'] for item in combined]
    if totals:
        print(f"\nCombined statistics:")
        print(f"  Average per day: {sum(totals)/len(totals):.1f}")
        print(f"  Days with 0 items: {sum(1 for t in totals if t == 0)}")
        print(f"  Days with 1-2 items: {sum(1 for t in totals if 1 <= t <= 2)}")
        print(f"  Days with 3-5 items: {sum(1 for t in totals if 3 <= t <= 5)}")
        print(f"  Days with 6+ items: {sum(1 for t in totals if t >= 6)}")

if __name__ == "__main__":
    try:
        analyze_daily_volume()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
