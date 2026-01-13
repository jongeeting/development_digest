#!/usr/bin/env python3
"""
Philadelphia Development Digest Generator

Generates a weekly digest of:
1. By-right housing permits (filtered by unit threshold)
2. Notable zoning variance applications

Organized by council district and neighborhood.
"""

import requests
import re
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def get_permits(days=7, min_units=5):
    """
    Get residential building permits from the last N days.

    Args:
        days: Number of days to look back
        min_units: Minimum number of units to include

    Returns:
        List of permit dictionaries
    """
    sql = f"""
    SELECT
        permitnumber,
        address,
        council_district,
        permittype,
        typeofwork,
        numberofunits,
        contractorname as developer,
        approvedscopeofwork,
        permitissuedate
    FROM permits
    WHERE commercialorresidential = 'Residential'
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '{days} days')
    AND numberofunits IS NOT NULL
    AND CAST(numberofunits AS INTEGER) >= {min_units}
    AND typeofwork = 'New Construction'
    ORDER BY council_district, permitissuedate DESC
    """

    result = query_carto(sql)
    return result.get('rows', [])

def get_appeals(days=7):
    """
    Get zoning variance applications from the last N days.

    Args:
        days: Number of days to look back

    Returns:
        List of appeal dictionaries
    """
    sql = f"""
    SELECT
        appealnumber,
        address,
        council_district,
        appealtype,
        applicationtype,
        appealgrounds,
        createddate,
        primaryappellant
    FROM appeals
    WHERE createddate >= (CURRENT_DATE - INTERVAL '{days} days')
    AND (
        applicationtype LIKE '%ZBA%'
        OR appealtype LIKE '%Variance%'
        OR LOWER(appealgrounds) LIKE '%variance%'
    )
    ORDER BY council_district, createddate DESC
    """

    result = query_carto(sql)
    return result.get('rows', [])

def extract_unit_count_from_text(text):
    """Try to extract unit count from permit description."""
    if not text:
        return None

    # Look for patterns like "10 units", "ten dwelling units", etc.
    patterns = [
        r'(\d+)[\s-]*(unit|dwelling)',
        r'(single|two|three|four|five|six|seven|eight|nine|ten)[\s-]*(family|unit)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            return matches[0]
    return None

def group_by_district(items, district_key='council_district'):
    """Group items by council district."""
    grouped = defaultdict(list)

    for item in items:
        district = item.get(district_key) or 'Unknown'
        grouped[district].append(item)

    return grouped

def format_permit_markdown(permit):
    """Format a single permit as markdown."""
    address = permit.get('address', 'N/A')
    units = permit.get('numberofunits', 'N/A')
    developer = permit.get('developer', 'N/A')
    permit_num = permit.get('permitnumber', 'N/A')

    # Create link to permit details (L&I permit search)
    permit_link = f"https://li.phila.gov/#details?entity=permits&eid={permit_num}"

    lines = [
        f"- **{address}** | Units: {units} | Developer: {developer}",
        f"  - [View permit details]({permit_link})"
    ]

    return '\n'.join(lines)

def format_appeal_markdown(appeal):
    """Format a single appeal as markdown."""
    address = appeal.get('address', 'N/A')
    appeal_num = appeal.get('appealnumber', 'N/A')
    appellant = appeal.get('primaryappellant', 'N/A')

    # Extract variance type from grounds
    grounds = appeal.get('appealgrounds', '')
    if grounds:
        # Truncate and clean up grounds text
        grounds_clean = grounds[:150].replace('\n', ' ').replace('\r', ' ')
        variance_desc = f"{grounds_clean}..."
    else:
        variance_desc = "Variance details not available"

    lines = [
        f"- **{address}**",
        f"  - Appeal: {appeal_num} | Appellant: {appellant}",
        f"  - Requested variance: {variance_desc}"
    ]

    return '\n'.join(lines)

def generate_digest(start_date=None, end_date=None, min_units=5):
    """
    Generate the full weekly digest.

    Args:
        start_date: Start date for the digest period (datetime or None for 7 days ago)
        end_date: End date for the digest period (datetime or None for today)
        min_units: Minimum number of units for permits

    Returns:
        Markdown-formatted digest string
    """
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=7)

    # Calculate days to look back
    days_back = (end_date - start_date).days + 1

    # Get data
    permits = get_permits(days=days_back, min_units=min_units)
    appeals = get_appeals(days=days_back)

    # Format date range
    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

    # Start building the markdown
    md = []
    md.append(f"# PHILADELPHIA DEVELOPMENT DIGEST")
    md.append(f"Week of {date_range}")
    md.append("")
    md.append("## SUMMARY")
    md.append(f"- {len(permits)} new by-right housing permits ({min_units}+ units)")
    md.append(f"- {len(appeals)} zoning variance applications filed")
    md.append("")

    # Optional: Add a one-line highlight if there's something notable
    if permits:
        largest = max(permits, key=lambda p: int(p.get('numberofunits', 0) or 0))
        units = largest.get('numberofunits', 'N/A')
        addr = largest.get('address', 'N/A')
        district = largest.get('council_district', 'N/A')
        md.append(f"**Largest project:** {units}-unit development at {addr} (District {district})")
        md.append("")

    # BY-RIGHT HOUSING PERMITS
    md.append("## BY-RIGHT HOUSING PERMITS")
    md.append("")

    if permits:
        grouped_permits = group_by_district(permits)

        # Sort districts numerically
        districts = sorted(grouped_permits.keys(),
                         key=lambda x: int(x) if x.isdigit() else 999)

        for district in districts:
            district_permits = grouped_permits[district]
            md.append(f"### COUNCIL DISTRICT {district}")
            md.append("")

            for permit in district_permits:
                md.append(format_permit_markdown(permit))
                md.append("")
    else:
        md.append(f"No permits with {min_units}+ units found in the last {days_back} days.")
        md.append("")

    # ZONING VARIANCE APPLICATIONS
    md.append("## ZONING VARIANCE APPLICATIONS")
    md.append("")

    if appeals:
        grouped_appeals = group_by_district(appeals)

        # Sort districts numerically
        districts = sorted(grouped_appeals.keys(),
                         key=lambda x: int(x) if x != 'Unknown' and str(x).isdigit() else 999)

        for district in districts:
            district_appeals = grouped_appeals[district]
            md.append(f"### COUNCIL DISTRICT {district}")
            md.append("")

            for appeal in district_appeals:
                md.append(format_appeal_markdown(appeal))
                md.append("")
    else:
        md.append(f"No zoning variance applications found in the last {days_back} days.")
        md.append("")

    md.append("---")
    md.append("*Data source: City of Philadelphia L&I Open Data via CARTO API*")

    return '\n'.join(md)

def main():
    parser = argparse.ArgumentParser(
        description='Generate Philadelphia Development Digest'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )
    parser.add_argument(
        '--min-units',
        type=int,
        default=5,
        help='Minimum number of units to include (default: 5)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: prints to stdout)'
    )

    args = parser.parse_args()

    # Generate digest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    digest = generate_digest(
        start_date=start_date,
        end_date=end_date,
        min_units=args.min_units
    )

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(digest)
        print(f"Digest written to {args.output}")
    else:
        print(digest)

if __name__ == "__main__":
    main()
