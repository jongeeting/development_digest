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

# ArcGIS REST API endpoints
ARCGIS_PERMITS_URL = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/PERMITS/FeatureServer/0/query"
ARCGIS_APPEALS_URL = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/ArcGIS/rest/services/APPEALS/FeatureServer/0/query"

# Legacy CARTO endpoint (kept for reference, not used)
API_BASE = "https://phl.carto.com/api/v2/sql"

class DataFreshnessWarning:
    """Container for data freshness warnings."""
    def __init__(self):
        self.warnings = []
        self.most_recent_permit = None
        self.most_recent_appeal = None

    def add_warning(self, message):
        self.warnings.append(message)

    def has_warnings(self):
        return len(self.warnings) > 0

def query_arcgis(url, params, timeout=30):
    """
    Execute a query against Philadelphia's ArcGIS FeatureServer.

    Args:
        url: The FeatureServer query endpoint
        params: Query parameters dict
        timeout: Request timeout in seconds

    Returns:
        List of feature attributes (normalized to look like CARTO rows)

    Raises:
        Exception: If API is unreachable or returns error
    """
    try:
        # Add default parameters
        params.setdefault('f', 'json')
        params.setdefault('outFields', '*')
        params.setdefault('returnGeometry', 'false')

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        # Check for ArcGIS errors
        if 'error' in data:
            raise Exception(f"ArcGIS API error: {data['error'].get('message', 'Unknown error')}")

        # Convert ArcGIS features to CARTO-like rows format
        features = data.get('features', [])
        rows = []
        for feature in features:
            attrs = feature.get('attributes', {})
            # Convert timestamp fields from milliseconds to ISO format for consistency
            for key, value in attrs.items():
                if value and 'date' in key.lower() and isinstance(value, (int, float)):
                    # Convert millisecond timestamp to datetime
                    attrs[key] = datetime.fromtimestamp(value / 1000).isoformat()
            rows.append(attrs)

        return rows

    except requests.exceptions.Timeout:
        raise Exception("City ArcGIS API timed out. The service may be temporarily unavailable.")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to City ArcGIS API. Check your internet connection or the API may be down.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"City ArcGIS API returned error: {e}")

def check_data_freshness():
    """
    Check how recent the permit and variance data is.

    Returns:
        tuple: (most_recent_permit_date, most_recent_appeal_date, days_old_permits, days_old_appeals)
    """
    try:
        # Check most recent permit from ArcGIS
        permit_params = {
            'where': '1=1',
            'outFields': 'permitissuedate',
            'orderByFields': 'permitissuedate DESC',
            'resultRecordCount': 1
        }
        permit_rows = query_arcgis(ARCGIS_PERMITS_URL, permit_params)
        most_recent_permit = permit_rows[0]['permitissuedate'] if permit_rows else None

        # Check most recent appeal from ArcGIS
        appeal_params = {
            'where': '1=1',
            'outFields': 'createddate',
            'orderByFields': 'createddate DESC',
            'resultRecordCount': 1
        }
        appeal_rows = query_arcgis(ARCGIS_APPEALS_URL, appeal_params)
        most_recent_appeal = appeal_rows[0]['createddate'] if appeal_rows else None

        # Calculate age in days
        from dateutil import parser as date_parser
        import pytz
        now = datetime.now(pytz.UTC)

        days_old_permits = None
        if most_recent_permit:
            permit_date = date_parser.parse(most_recent_permit)
            # Make timezone-aware if it isn't already
            if permit_date.tzinfo is None:
                permit_date = pytz.UTC.localize(permit_date)
            days_old_permits = (now - permit_date).days

        days_old_appeals = None
        if most_recent_appeal:
            appeal_date = date_parser.parse(most_recent_appeal)
            # Make timezone-aware if it isn't already
            if appeal_date.tzinfo is None:
                appeal_date = pytz.UTC.localize(appeal_date)
            days_old_appeals = (now - appeal_date).days

        return most_recent_permit, most_recent_appeal, days_old_permits, days_old_appeals
    except Exception as e:
        # If we can't check freshness, return None
        return None, None, None, None

def get_permits(days=7, min_units=1):
    """
    Get residential building permits from the last N days.

    Args:
        days: Number of days to look back
        min_units: Minimum number of units to include

    Returns:
        List of permit dictionaries with unit counts (from field or extracted)
    """
    # Calculate date threshold (N days ago)
    threshold_date = datetime.now() - timedelta(days=days)
    threshold_str = threshold_date.strftime('%Y-%m-%d %H:%M:%S')

    # Query ArcGIS for residential permits (new construction and conversions)
    # Include Change of Use permits regardless of commercial/residential flag
    # because conversions TO residential are marked as "Commercial"
    params = {
        'where': f"((commercialorresidential = 'Residential' AND typeofwork = 'New Construction') OR (typeofwork = 'Change of Use')) AND permitissuedate >= TIMESTAMP '{threshold_str}'",
        'outFields': 'permitnumber,address,council_district,permittype,typeofwork,numberofunits,contractorname,approvedscopeofwork,permitissuedate,permitdescription,commercialorresidential',
        'orderByFields': 'council_district,permitissuedate DESC'
    }

    all_permits = query_arcgis(ARCGIS_PERMITS_URL, params)

    # For Change of Use permits, filter to only those converting TO residential
    permits = []
    for permit in all_permits:
        typeofwork = permit.get('typeofwork', '')
        scope = (permit.get('approvedscopeofwork', '') or '').lower()

        # Include New Construction residential permits
        if typeofwork == 'New Construction':
            permits.append(permit)
        # Include Change of Use only if scope mentions residential
        elif typeofwork == 'Change of Use' and 'residential' in scope:
            permits.append(permit)

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
        # Map contractorname to developer for consistency
        if 'contractorname' in permit and 'developer' not in permit:
            permit['developer'] = permit['contractorname']

        # Use field value if available, otherwise try extraction
        units = permit.get('numberofunits')
        if not units:
            # Try extracting from approvedscopeofwork first
            extracted = extract_unit_count_from_text(permit.get('approvedscopeofwork'))
            if not extracted:
                # Also try permitdescription field
                extracted = extract_unit_count_from_text(permit.get('permitdescription'))

            if extracted:
                permit['numberofunits'] = extracted
                permit['units_source'] = 'extracted'
            else:
                # For Zoning Permits (ZP-*) with "Multi-Family" but no unit count,
                # flag as "Unknown" but include them since they're likely significant
                scope = permit.get('approvedscopeofwork', '').lower()
                permit_num = permit.get('permitnumber', '')
                if permit_num.startswith('ZP-') and 'multi-family' in scope:
                    permit['numberofunits'] = 'Unknown (Multi-Family)'
                    permit['units_source'] = 'zoning_multifamily'
                else:
                    permit['units_source'] = 'unknown'
        else:
            units = int(units)
            permit['numberofunits'] = units
            permit['units_source'] = 'field'

        # Filter by minimum units
        # Include if: has unit count >= min_units, OR is a multi-family zoning permit with unknown units
        has_units = permit.get('numberofunits')
        if has_units:
            if isinstance(has_units, str) and 'Unknown' in has_units:
                # Include multi-family zoning permits even without specific unit count
                filtered_permits.append(permit)
            elif int(has_units) >= min_units:
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
    # Calculate date threshold (N days ago)
    threshold_date = datetime.now() - timedelta(days=days)
    threshold_str = threshold_date.strftime('%Y-%m-%d %H:%M:%S')

    # Query ArcGIS for variance appeals
    # Note: ArcGIS doesn't support LIKE with wildcards in the same way, so we use broader filter
    params = {
        'where': f"createddate >= TIMESTAMP '{threshold_str}' AND (UPPER(applicationtype) LIKE '%ZBA%' OR UPPER(appealtype) LIKE '%VARIANCE%' OR UPPER(appealgrounds) LIKE '%VARIANCE%')",
        'outFields': 'appealnumber,address,council_district,appealtype,applicationtype,appealgrounds,createddate,primaryappellant',
        'orderByFields': 'council_district,createddate DESC'
    }

    appeals = query_arcgis(ARCGIS_APPEALS_URL, params)

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

    # Check data freshness
    freshness_warnings = DataFreshnessWarning()
    most_recent_permit, most_recent_appeal, days_old_permits, days_old_appeals = check_data_freshness()

    # Add warnings if data is stale (more than 3 days old on weekdays)
    if days_old_permits is not None and days_old_permits > 3:
        from dateutil import parser as date_parser
        permit_date_obj = date_parser.parse(most_recent_permit)
        permit_date_str = permit_date_obj.strftime('%B %d, %Y')
        freshness_warnings.add_warning(f"⚠️ Permit data last updated: {permit_date_str} ({days_old_permits} days ago)")
        freshness_warnings.most_recent_permit = permit_date_str

    if days_old_appeals is not None and days_old_appeals > 3:
        from dateutil import parser as date_parser
        appeal_date_obj = date_parser.parse(most_recent_appeal)
        appeal_date_str = appeal_date_obj.strftime('%B %d, %Y')
        freshness_warnings.add_warning(f"⚠️ Variance data last updated: {appeal_date_str} ({days_old_appeals} days ago)")
        freshness_warnings.most_recent_appeal = appeal_date_str

    # Get data
    try:
        permits = get_permits(days=days_back, min_units=min_units)
    except Exception as e:
        freshness_warnings.add_warning(f"❌ Error fetching permits: {str(e)}")
        permits = []

    try:
        appeals = get_appeals(days=days_back)
    except Exception as e:
        freshness_warnings.add_warning(f"❌ Error fetching variances: {str(e)}")
        appeals = []

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
        units = p.get('numberofunits')
        if units:
            # Skip if units is unknown/string
            if isinstance(units, (int, float)) or (isinstance(units, str) and units.isdigit()):
                all_projects.append({
                    'units': int(units),
                    'address': p.get('address', 'N/A'),
                    'district': p.get('council_district', 'N/A'),
                    'type': 'by-right permit'
                })
    for a in appeals:
        units = a.get('numberofunits')
        if units:
            # Skip if units is unknown/string
            if isinstance(units, (int, float)) or (isinstance(units, str) and units.isdigit()):
                all_projects.append({
                    'units': int(units),
                    'address': a.get('address', 'N/A'),
                    'district': a.get('council_district', 'N/A'),
                    'type': 'variance application'
                })

    # Build digest based on output format
    if html:
        return generate_html_digest(permits, appeals, all_projects, date_range, min_units, days_back, freshness_warnings)
    else:
        return generate_markdown_digest(permits, appeals, all_projects, date_range, min_units, days_back, freshness_warnings)

def generate_markdown_digest(permits, appeals, all_projects, date_range, min_units, days_back, freshness_warnings=None):
    """Generate markdown formatted digest."""
    md = []
    md.append(f"# PHILADELPHIA DEVELOPMENT DIGEST")
    md.append(f"Week of {date_range}")
    md.append("")

    # Add data freshness warnings if present
    if freshness_warnings and freshness_warnings.has_warnings():
        md.append("## DATA STATUS")
        for warning in freshness_warnings.warnings:
            md.append(f"{warning}")
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
    md.append("*Data source: City of Philadelphia L&I Open Data via ArcGIS*")

    return '\n'.join(md)

def generate_html_digest(permits, appeals, all_projects, date_range, min_units, days_back, freshness_warnings=None):
    """Generate HTML formatted digest."""
    html = []
    html.append("<h1>PHILADELPHIA DEVELOPMENT DIGEST</h1>")
    html.append(f"<p>Week of {date_range}</p>")

    # Add data freshness warnings if present
    if freshness_warnings and freshness_warnings.has_warnings():
        html.append("<h2>DATA STATUS</h2>")
        html.append("<div style='background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin-bottom: 20px;'>")
        for warning in freshness_warnings.warnings:
            html.append(f"<p style='margin: 4px 0;'>{warning}</p>")
        html.append("</div>")

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
    html.append("<p><em>Data source: City of Philadelphia L&I Open Data via ArcGIS</em></p>")

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
