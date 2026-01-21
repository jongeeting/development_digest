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

def get_permits(days=7, min_units=1):
    """
    Get residential building permits from the last N days.

    Args:
        days: Number of days to look back
        min_units: Minimum number of units to include

    Returns:
        List of permit dictionaries with unit counts (from field or extracted)
    """
    # First get all new construction permits
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
    AND typeofwork = 'New Construction'
    ORDER BY council_district, permitissuedate DESC
    """

    result = query_carto(sql)
    permits = result.get('rows', [])

    # Deduplicate permits by permit number (keep most recent)
    seen_permits = {}
    for permit in permits:
        permit_num = permit.get('permitnumber')
        if permit_num:
            # Keep the permit with the most recent issue date
            if permit_num not in seen_permits:
                seen_permits[permit_num] = permit
            else:
                # Compare dates and keep the newer one
                existing_date = seen_permits[permit_num].get('permitissuedate', '')
                new_date = permit.get('permitissuedate', '')
                if new_date > existing_date:
                    seen_permits[permit_num] = permit

    # Use deduplicated permits
    permits = list(seen_permits.values())

    # Enhance permits with extracted unit counts
    filtered_permits = []
    for permit in permits:
        # Use field value if available, otherwise try extraction
        units = permit.get('numberofunits')
        if not units:
            extracted = extract_unit_count_from_text(permit.get('approvedscopeofwork'))
            if extracted:
                permit['numberofunits'] = extracted
                permit['units_source'] = 'extracted'
            else:
                permit['units_source'] = 'unknown'
        else:
            units = int(units)
            permit['numberofunits'] = units
            permit['units_source'] = 'field'

        # Filter by minimum units
        if permit.get('numberofunits') and int(permit['numberofunits']) >= min_units:
            filtered_permits.append(permit)

    return filtered_permits

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
    appeals = result.get('rows', [])

    # Deduplicate appeals by appeal number (keep most recent)
    seen_appeals = {}
    for appeal in appeals:
        appeal_num = appeal.get('appealnumber')
        if appeal_num:
            # Keep the appeal with the most recent created date
            if appeal_num not in seen_appeals:
                seen_appeals[appeal_num] = appeal
            else:
                # Compare dates and keep the newer one
                existing_date = seen_appeals[appeal_num].get('createddate', '')
                new_date = appeal.get('createddate', '')
                if new_date > existing_date:
                    seen_appeals[appeal_num] = appeal

    return list(seen_appeals.values())

def extract_unit_count_from_text(text):
    """Try to extract unit count from permit description."""
    if not text:
        return None

    text_lower = text.lower()
    matches = []

    # Pattern 1: "X unit(s)" or "X dwelling(s)" - with optional 's' and parentheses
    # Matches: "19 unit", "(8) dwelling units", "five dwelling units"
    pattern1 = re.findall(r'\(?(\d+)\)?[\s-]+(unit|dwelling)s?\b', text_lower)
    if pattern1:
        matches.extend([int(m[0]) for m in pattern1])

    # Pattern 2: "X-family" or "X family" with number (handles multifamily, multi-family)
    # Matches: "8-family", "19 family", "eight (8) family"
    pattern2 = re.findall(r'\(?(\d+)\)?[\s-]*(?:family|household)', text_lower)
    if pattern2:
        matches.extend([int(m) for m in pattern2])

    # Pattern 3: Word numbers with family/dwelling/unit
    # Matches: "eight family", "nineteen unit", "five dwelling"
    family_words = {
        'single': 1, 'one': 1,
        'two': 2, 'double': 2,
        'three': 3, 'triple': 3,
        'four': 4, 'quad': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20
    }

    for word, count in family_words.items():
        # Match word numbers before family/dwelling/unit (with lots of variation)
        if re.search(rf'\b{word}\b.*?(family|dwelling|unit)', text_lower):
            matches.append(count)

    # Return the maximum count found (most specific)
    return max(matches) if matches else None

def group_by_district(items, district_key='council_district'):
    """Group items by council district."""
    grouped = defaultdict(list)

    for item in items:
        district = item.get(district_key) or 'Unknown'
        grouped[district].append(item)

    return grouped

def format_permit_markdown(permit, html=False):
    """Format a single permit as markdown or HTML."""
    address = permit.get('address', 'N/A')
    units = permit.get('numberofunits', 'N/A')
    developer = permit.get('developer', 'N/A')
    permit_num = permit.get('permitnumber', 'N/A')

    # Create link to permit details (L&I permit search)
    permit_link = f"https://li.phila.gov/#details?entity=permits&eid={permit_num}"

    if html:
        return f"""<li><strong>{address} | Units: {units} | Developer: {developer}</strong>
<ul>
<li><a href="{permit_link}">View permit details</a></li>
</ul>
</li>"""
    else:
        lines = [
            f"- **{address}** | Units: {units} | Developer: {developer}",
            f"  - [View permit details]({permit_link})"
        ]
        return '\n'.join(lines)

def format_appeal_markdown(appeal, html=False):
    """Format a single appeal as markdown or HTML."""
    address = appeal.get('address', 'N/A')
    appeal_num = appeal.get('appealnumber', 'N/A')
    appellant = appeal.get('primaryappellant', 'N/A')

    # Extract variance type from grounds
    grounds = appeal.get('appealgrounds', '')

    # Try to extract unit count from grounds
    units = extract_unit_count_from_text(grounds)
    units_str = f" | {units} units" if units and units >= 5 else ""

    if grounds:
        # Clean up grounds text - replace newlines/returns but keep full text
        variance_desc = grounds.replace('\n', ' ').replace('\r', ' ').strip()
    else:
        variance_desc = "Variance details not available"

    if html:
        return f"""<li><strong>{address}{units_str}</strong>
<ul>
<li>Appeal: {appeal_num} | Appellant: {appellant}</li>
<li>Requested variance: {variance_desc}</li>
</ul>
</li>"""
    else:
        lines = [
            f"- **{address}{units_str}**",
            f"  - Appeal: {appeal_num} | Appellant: {appellant}",
            f"  - Requested variance: {variance_desc}"
        ]
        return '\n'.join(lines)

def generate_digest(start_date=None, end_date=None, min_units=1, html=False):
    """
    Generate the full weekly digest.

    Args:
        start_date: Start date for the digest period (datetime or None for 7 days ago)
        end_date: End date for the digest period (datetime or None for today)
        min_units: Minimum number of units for permits
        html: Generate HTML output instead of markdown (default: False)

    Returns:
        Markdown or HTML formatted digest string
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

    # Extract unit counts from appeals
    for appeal in appeals:
        units = extract_unit_count_from_text(appeal.get('appealgrounds', ''))
        if units:
            appeal['numberofunits'] = units

    # Format date range
    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"

    # Find largest project across BOTH permits and appeals
    all_projects = []
    for p in permits:
        if p.get('numberofunits'):
            all_projects.append({
                'units': int(p.get('numberofunits', 0)),
                'address': p.get('address', 'N/A'),
                'district': p.get('council_district', 'N/A'),
                'type': 'by-right permit'
            })
    for a in appeals:
        if a.get('numberofunits'):
            all_projects.append({
                'units': int(a.get('numberofunits', 0)),
                'address': a.get('address', 'N/A'),
                'district': a.get('council_district', 'N/A'),
                'type': 'variance application'
            })

    # Build digest based on output format
    if html:
        return generate_html_digest(permits, appeals, all_projects, date_range, min_units, days_back)
    else:
        return generate_markdown_digest(permits, appeals, all_projects, date_range, min_units, days_back)

def generate_markdown_digest(permits, appeals, all_projects, date_range, min_units, days_back):
    """Generate markdown formatted digest."""
    md = []
    md.append(f"# PHILADELPHIA DEVELOPMENT DIGEST")
    md.append(f"Week of {date_range}")
    md.append("")
    md.append("## SUMMARY")
    md.append(f"- {len(permits)} new by-right housing permits ({min_units}+ units)")
    md.append(f"- {len(appeals)} zoning variance applications filed")
    md.append("")

    if all_projects:
        largest = max(all_projects, key=lambda x: x['units'])
        md.append(f"**Largest project:** {largest['units']}-unit {largest['type']} at {largest['address']} (District {largest['district']})")
        md.append("")

    # BY-RIGHT HOUSING PERMITS
    md.append("## BY-RIGHT HOUSING PERMITS")
    md.append("")

    if permits:
        grouped_permits = group_by_district(permits)
        districts = sorted(grouped_permits.keys(),
                         key=lambda x: int(x) if x.isdigit() else 999)

        for district in districts:
            district_permits = grouped_permits[district]
            md.append(f"### COUNCIL DISTRICT {district}")
            md.append("")

            for permit in district_permits:
                md.append(format_permit_markdown(permit, html=False))
                md.append("")
    else:
        md.append(f"No permits with {min_units}+ units found in the last {days_back} days.")
        md.append("")

    # ZONING VARIANCE APPLICATIONS
    md.append("## ZONING VARIANCE APPLICATIONS")
    md.append("")

    if appeals:
        grouped_appeals = group_by_district(appeals)
        districts = sorted(grouped_appeals.keys(),
                         key=lambda x: int(x) if x != 'Unknown' and str(x).isdigit() else 999)

        for district in districts:
            district_appeals = grouped_appeals[district]
            md.append(f"### COUNCIL DISTRICT {district}")
            md.append("")

            for appeal in district_appeals:
                md.append(format_appeal_markdown(appeal, html=False))
                md.append("")
    else:
        md.append(f"No zoning variance applications found in the last {days_back} days.")
        md.append("")

    md.append("---")
    md.append("*Data source: City of Philadelphia L&I Open Data via CARTO API*")

    return '\n'.join(md)

def generate_html_digest(permits, appeals, all_projects, date_range, min_units, days_back):
    """Generate HTML formatted digest."""
    html = []
    html.append("<h1>PHILADELPHIA DEVELOPMENT DIGEST</h1>")
    html.append(f"<p>Week of {date_range}</p>")
    html.append("<h2>SUMMARY</h2>")
    html.append("<ul>")
    html.append(f"<li>{len(permits)} new by-right housing permits ({min_units}+ units)</li>")
    html.append(f"<li>{len(appeals)} zoning variance applications filed</li>")
    html.append("</ul>")

    if all_projects:
        largest = max(all_projects, key=lambda x: x['units'])
        html.append(f"<p><strong>Largest project:</strong> {largest['units']}-unit {largest['type']} at {largest['address']} (District {largest['district']})</p>")

    # BY-RIGHT HOUSING PERMITS
    html.append("<h2>BY-RIGHT HOUSING PERMITS</h2>")

    if permits:
        grouped_permits = group_by_district(permits)
        districts = sorted(grouped_permits.keys(),
                         key=lambda x: int(x) if x.isdigit() else 999)

        for district in districts:
            district_permits = grouped_permits[district]
            html.append(f"<h3>COUNCIL DISTRICT {district}</h3>")
            html.append("<ul>")

            for permit in district_permits:
                html.append(format_permit_markdown(permit, html=True))

            html.append("</ul>")
    else:
        html.append(f"<p>No permits with {min_units}+ units found in the last {days_back} days.</p>")

    # ZONING VARIANCE APPLICATIONS
    html.append("<h2>ZONING VARIANCE APPLICATIONS</h2>")

    if appeals:
        grouped_appeals = group_by_district(appeals)
        districts = sorted(grouped_appeals.keys(),
                         key=lambda x: int(x) if x != 'Unknown' and str(x).isdigit() else 999)

        for district in districts:
            district_appeals = grouped_appeals[district]
            html.append(f"<h3>COUNCIL DISTRICT {district}</h3>")
            html.append("<ul>")

            for appeal in district_appeals:
                html.append(format_appeal_markdown(appeal, html=True))

            html.append("</ul>")
    else:
        html.append(f"<p>No zoning variance applications found in the last {days_back} days.</p>")

    html.append("<hr>")
    html.append("<p><em>Data source: City of Philadelphia L&I Open Data via CARTO API</em></p>")

    return '\n'.join(html)

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
        default=1,
        help='Minimum number of units to include (default: 1)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: prints to stdout)'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML output instead of Markdown (better for pasting into Substack)'
    )

    args = parser.parse_args()

    # Generate digest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    digest = generate_digest(
        start_date=start_date,
        end_date=end_date,
        min_units=args.min_units,
        html=args.html
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
