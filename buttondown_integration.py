#!/usr/bin/env python3
"""
Buttondown email service integration with geographic filtering.
"""

import os
import requests
from datetime import datetime, timedelta
from geographic_matcher import GeographicMatcher
import json

BUTTONDOWN_API_KEY = os.environ.get('BUTTONDOWN_API_KEY')
BUTTONDOWN_API_BASE = 'https://api.buttondown.email/v1'

class ButtondownService:
    """Manage Buttondown subscribers and send filtered emails."""

    def __init__(self, api_key=None):
        self.api_key = api_key or BUTTONDOWN_API_KEY
        if not self.api_key:
            raise ValueError("BUTTONDOWN_API_KEY environment variable required")

        self.headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json'
        }

    def get_subscribers(self):
        """Get all subscribers with their tags/metadata."""
        response = requests.get(
            f'{BUTTONDOWN_API_BASE}/subscribers',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['results']

    def get_subscriber_preferences(self, subscriber):
        """
        Extract geographic preferences from subscriber metadata.

        Buttondown stores this in subscriber.metadata as JSON:
        {
            "neighborhoods": ["Fishtown", "Northern Liberties"],
            "districts": ["1", "5"],
            "frequency": "daily"
        }

        Returns dict with preferences
        """
        metadata = subscriber.get('metadata', {})

        # Parse metadata if it's a string
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}

        return {
            'email': subscriber.get('email'),
            'neighborhoods': metadata.get('neighborhoods', []),
            'districts': metadata.get('districts', []),
            'frequency': metadata.get('frequency', 'weekly'),
            'active': subscriber.get('subscriber_type') == 'regular'
        }

    def group_subscribers_by_preferences(self):
        """
        Group subscribers by their geographic preferences.

        Returns dict like:
        {
            'citywide': [email1, email2],
            'neighborhoods': {
                'Fishtown': [email3],
                'Northern Liberties': [email3, email4]
            },
            'districts': {
                '1': [email5],
                '5': [email6, email7]
            }
        }
        """
        subscribers = self.get_subscribers()

        groups = {
            'citywide': [],
            'neighborhoods': {},
            'districts': {}
        }

        for sub in subscribers:
            prefs = self.get_subscriber_preferences(sub)

            # Skip inactive or non-daily subscribers
            if not prefs['active'] or prefs['frequency'] != 'daily':
                continue

            email = prefs['email']

            # Citywide subscribers
            if (not prefs['neighborhoods'] and not prefs['districts']):
                groups['citywide'].append(email)
                continue

            # Neighborhood-specific subscribers
            for neighborhood in prefs['neighborhoods']:
                if neighborhood not in groups['neighborhoods']:
                    groups['neighborhoods'][neighborhood] = []
                groups['neighborhoods'][neighborhood].append(email)

            # District-specific subscribers
            for district in prefs['districts']:
                if district not in groups['districts']:
                    groups['districts'][district] = []
                groups['districts'][district].append(email)

        return groups

    def send_email(self, subject, body, recipients=None, segment=None):
        """
        Send email via Buttondown.

        Args:
            subject: Email subject line
            body: Email body (markdown)
            recipients: List of email addresses (for targeted send)
            segment: Buttondown segment/tag (alternative to recipients)
        """
        payload = {
            'subject': subject,
            'body': body,
            'email_type': 'public'  # or 'private' for paid subscribers only
        }

        # Either send to specific recipients or a segment
        if recipients:
            # For targeted sends, we need to use the draft + schedule approach
            # or send individual emails (Buttondown limitation)
            payload['recipients'] = recipients
        elif segment:
            payload['segment'] = segment

        response = requests.post(
            f'{BUTTONDOWN_API_BASE}/emails',
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        return response.json()

    def send_filtered_daily_digests(self, permits, variances):
        """
        Send daily digests filtered by subscriber preferences.

        Args:
            permits: List of permits with neighborhood data
            variances: List of variances with neighborhood data
        """
        from generate_digest import format_permit_markdown, format_appeal_markdown

        # Get subscriber groups
        groups = self.group_subscribers_by_preferences()

        matcher = GeographicMatcher()
        sent_count = 0

        # 1. Send citywide digest
        if groups['citywide']:
            body = self._format_daily_digest(permits, variances, 'Citywide')
            subject = f"Philadelphia Development Daily - {datetime.now().strftime('%b %d, %Y')}"

            # Buttondown doesn't support batch sends easily, so we send as a public email
            # that only daily subscribers receive (managed via tags)
            self.send_email(subject, body, segment='daily-citywide')
            sent_count += len(groups['citywide'])
            print(f"✓ Sent citywide digest to {len(groups['citywide'])} subscribers")

        # 2. Send neighborhood-specific digests
        for neighborhood, emails in groups['neighborhoods'].items():
            # Filter items to this neighborhood
            filtered_permits = matcher.filter_by_neighborhoods(permits, [neighborhood])
            filtered_variances = matcher.filter_by_neighborhoods(variances, [neighborhood])

            # Skip if no activity
            if not filtered_permits and not filtered_variances:
                print(f"  ⊘ No activity in {neighborhood}, skipping")
                continue

            body = self._format_daily_digest(
                filtered_permits,
                filtered_variances,
                f"{neighborhood} Neighborhood"
            )
            subject = f"{neighborhood} Development Daily - {datetime.now().strftime('%b %d, %Y')}"

            # Send to this neighborhood's subscribers
            # Note: Buttondown may require individual sends for custom recipient lists
            for email in emails:
                self.send_email(subject, body, recipients=[email])

            sent_count += len(emails)
            print(f"✓ Sent {neighborhood} digest to {len(emails)} subscribers ({len(filtered_permits)} permits, {len(filtered_variances)} variances)")

        # 3. Send district-specific digests
        for district, emails in groups['districts'].items():
            # Filter items to this district
            filtered_permits = matcher.filter_by_districts(permits, [district])
            filtered_variances = matcher.filter_by_districts(variances, [district])

            # Skip if no activity
            if not filtered_permits and not filtered_variances:
                print(f"  ⊘ No activity in District {district}, skipping")
                continue

            body = self._format_daily_digest(
                filtered_permits,
                filtered_variances,
                f"Council District {district}"
            )
            subject = f"District {district} Development Daily - {datetime.now().strftime('%b %d, %Y')}"

            for email in emails:
                self.send_email(subject, body, recipients=[email])

            sent_count += len(emails)
            print(f"✓ Sent District {district} digest to {len(emails)} subscribers ({len(filtered_permits)} permits, {len(filtered_variances)} variances)")

        print(f"\n✓ Total emails sent: {sent_count}")
        return sent_count

    def _format_daily_digest(self, permits, variances, area_name):
        """Format daily digest email body."""
        from generate_digest import format_permit_markdown, format_appeal_markdown

        date_str = datetime.now().strftime('%A, %B %d, %Y')

        lines = []
        lines.append(f"# Philadelphia Development Daily")
        lines.append(f"## {area_name}")
        lines.append(f"{date_str}\n")

        # Permits section
        lines.append(f"## NEW CONSTRUCTION PERMITS ({len(permits)})\n")
        if permits:
            for permit in permits:
                lines.append(format_permit_markdown(permit))
                lines.append("")
        else:
            lines.append("No new construction permits filed yesterday.\n")

        # Variances section
        lines.append(f"## ZONING VARIANCES FILED ({len(variances)})\n")
        if variances:
            for variance in variances:
                lines.append(format_appeal_markdown(variance))
                lines.append("")
        else:
            lines.append("No zoning variance applications filed yesterday.\n")

        lines.append("---")
        lines.append("*Data source: City of Philadelphia L&I Open Data via CARTO API*")

        return '\n'.join(lines)

if __name__ == "__main__":
    """Test Buttondown integration."""
    print("Buttondown Integration Test")
    print("=" * 80)

    if not BUTTONDOWN_API_KEY:
        print("⚠ BUTTONDOWN_API_KEY not set. Set it in your environment:")
        print("  export BUTTONDOWN_API_KEY='your-api-key-here'")
        print("\nGet your API key from: https://buttondown.email/settings")
        exit(1)

    service = ButtondownService()

    print("\nFetching subscribers...")
    try:
        subscribers = service.get_subscribers()
        print(f"✓ Found {len(subscribers)} subscribers")

        # Show subscriber preferences
        for sub in subscribers[:5]:  # Show first 5
            prefs = service.get_subscriber_preferences(sub)
            print(f"\n  {prefs['email']}:")
            print(f"    Frequency: {prefs['frequency']}")
            print(f"    Neighborhoods: {prefs['neighborhoods'] or 'All (citywide)'}")
            print(f"    Districts: {prefs['districts'] or 'All (citywide)'}")

    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure your API key is valid!")
