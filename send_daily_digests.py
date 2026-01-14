#!/usr/bin/env python3
"""
Generate and send daily digests filtered by subscriber geographic preferences.
"""

import argparse
from datetime import datetime, timedelta
from generate_digest import get_permits, get_appeals
from geographic_matcher import GeographicMatcher
from buttondown_integration import ButtondownService

def main():
    parser = argparse.ArgumentParser(
        description='Send daily development digests filtered by geography'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate digests but do not send emails'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days to look back (default: 1 for yesterday)'
    )

    args = parser.parse_args()

    print("Philadelphia Development Daily Digest Sender")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"Looking back: {args.days} day(s)")
    print(f"Mode: {'DRY RUN (no emails sent)' if args.dry_run else 'LIVE (sending emails)'}")
    print("=" * 80)

    # Step 1: Fetch permits and variances
    print("\n1. Fetching permits and variances...")
    permits = get_permits(days=args.days, min_units=1)
    variances = get_appeals(days=args.days)

    print(f"   ✓ Found {len(permits)} permits")
    print(f"   ✓ Found {len(variances)} variances")

    if not permits and not variances:
        print("\n⊘ No activity in the specified time period. No emails to send.")
        return

    # Step 2: Enrich with neighborhood data
    print("\n2. Matching permits/variances to neighborhoods...")
    matcher = GeographicMatcher()

    permits = matcher.enrich_items(permits)
    variances = matcher.enrich_items(variances)

    # Show geographic distribution
    neighborhoods = matcher.get_unique_neighborhoods(permits + variances)
    districts = matcher.get_unique_districts(permits + variances)

    print(f"   ✓ Activity in {len(neighborhoods)} neighborhoods")
    print(f"   ✓ Activity in {len(districts)} council districts")

    if neighborhoods:
        print(f"\n   Active neighborhoods: {', '.join(neighborhoods[:10])}")
        if len(neighborhoods) > 10:
            print(f"   ... and {len(neighborhoods) - 10} more")

    # Step 3: Send filtered emails
    print("\n3. Sending filtered digests to subscribers...")

    if args.dry_run:
        print("   DRY RUN MODE - Simulating email sends:")
        service = ButtondownService()
        groups = service.group_subscribers_by_preferences()

        print(f"   • Citywide: {len(groups['citywide'])} subscribers")
        for neighborhood, emails in list(groups['neighborhoods'].items())[:5]:
            filtered = matcher.filter_by_neighborhoods(permits + variances, [neighborhood])
            if filtered:
                print(f"   • {neighborhood}: {len(emails)} subscribers ({len(filtered)} items)")

        print("\n   ✓ Dry run complete. No emails sent.")

    else:
        service = ButtondownService()
        sent_count = service.send_filtered_daily_digests(permits, variances)
        print(f"\n   ✓ Sent {sent_count} emails total")

    print("\n" + "=" * 80)
    print("✓ Daily digest process complete!")

if __name__ == "__main__":
    main()
