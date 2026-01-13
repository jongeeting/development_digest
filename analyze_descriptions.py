#!/usr/bin/env python3
"""
Analyze project descriptions to see if unit counts can be extracted.
"""

import requests
import re
from collections import Counter

API_BASE = "https://phl.carto.com/api/v2/sql"

def query_carto(sql):
    """Execute a SQL query against Philadelphia's CARTO API."""
    params = {'q': sql, 'format': 'json'}
    response = requests.get(API_BASE, params=params)
    response.raise_for_status()
    return response.json()

def extract_unit_info(text):
    """Try to extract unit count from description text."""
    if not text:
        return None, []

    text_lower = text.lower()
    matches = []

    # Pattern 1: "X unit" or "X units"
    pattern1 = re.findall(r'\b(\d+)[\s-]+(unit|dwelling)', text_lower)
    if pattern1:
        matches.extend([(int(m[0]), f"{m[0]} {m[1]}") for m in pattern1])

    # Pattern 2: "single family", "two family", etc.
    family_words = {
        'single': 1, 'one': 1,
        'two': 2, 'double': 2,
        'three': 3, 'triple': 3,
        'four': 4, 'quad': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }

    for word, count in family_words.items():
        if re.search(rf'\b{word}[\s-]+family\b', text_lower):
            matches.append((count, f"{word} family"))

    # Pattern 3: "X-family"
    pattern3 = re.findall(r'\b(\d+)[\s-]+family\b', text_lower)
    if pattern3:
        matches.extend([(int(m), f"{m} family") for m in pattern3])

    # Return the most common match or first if tie
    if matches:
        # Get the most specific/largest number
        return max(matches, key=lambda x: x[0])

    return None, []

def analyze_recent_permits():
    """Analyze recent permits to see what we can extract from descriptions."""

    print("ANALYZING PROJECT DESCRIPTIONS (Last 14 days)")
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
    AND permitissuedate >= (CURRENT_DATE - INTERVAL '14 days')
    AND typeofwork = 'New Construction'
    ORDER BY permitissuedate DESC
    LIMIT 50
    """

    result = query_carto(sql)
    permits = result.get('rows', [])

    print(f"\nFound {len(permits)} new construction permits\n")

    # Statistics
    has_field = 0
    extracted_from_text = 0
    matches_field = 0
    mismatches = []

    print(f"{'Address':<35} {'Field':<6} {'Extracted':<15} {'Match':<6}")
    print("-" * 80)

    for permit in permits:
        address = permit.get('address', 'N/A')[:33]
        field_units = permit.get('numberofunits')
        scope = permit.get('approvedscopeofwork', '')

        # Extract from text
        extracted_info = extract_unit_info(scope)
        extracted_units = extracted_info[0] if extracted_info else None
        extracted_text = extracted_info[1] if extracted_info and len(extracted_info) > 1 else ''

        # Count statistics
        if field_units:
            has_field += 1

        if extracted_units:
            extracted_from_text += 1

        # Check for matches/mismatches
        match = '?'
        if field_units and extracted_units:
            if int(field_units) == extracted_units:
                match = '✓'
                matches_field += 1
            else:
                match = '✗'
                mismatches.append({
                    'address': address,
                    'field': field_units,
                    'extracted': extracted_units,
                    'text': extracted_text
                })
        elif not field_units and extracted_units:
            match = 'NEW'

        field_display = str(field_units) if field_units else '-'
        extracted_display = f"{extracted_units} ({extracted_text})" if extracted_units else '-'

        print(f"{address:<35} {field_display:<6} {extracted_display:<15} {match:<6}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total permits analyzed: {len(permits)}")
    print(f"Permits with numberofunits field: {has_field} ({has_field/len(permits)*100:.1f}%)")
    print(f"Permits with extractable unit info: {extracted_from_text} ({extracted_from_text/len(permits)*100:.1f}%)")
    print(f"Matches between field and extraction: {matches_field}")
    print(f"Mismatches: {len(mismatches)}")

    if mismatches:
        print("\n" + "=" * 80)
        print("MISMATCHES (Field vs Extracted)")
        print("=" * 80)
        for m in mismatches:
            print(f"\n{m['address']}")
            print(f"  Field: {m['field']} units")
            print(f"  Extracted: {m['extracted']} ({m['text']})")

    # Show some examples with rich descriptions
    print("\n" + "=" * 80)
    print("SAMPLE DESCRIPTIONS WITH UNIT INFO")
    print("=" * 80)

    for i, permit in enumerate(permits[:10], 1):
        scope = permit.get('approvedscopeofwork', '')
        if scope and len(scope) > 100:
            extracted = extract_unit_info(scope)
            print(f"\n{i}. {permit.get('address', 'N/A')}")
            print(f"   Field: {permit.get('numberofunits', 'N/A')} | Extracted: {extracted}")
            print(f"   Scope: {scope[:200]}...")

if __name__ == "__main__":
    try:
        analyze_recent_permits()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
