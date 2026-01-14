# Geographic Filtering Guide

Send personalized daily digests filtered by neighborhood or council district! Subscribers only receive updates for areas they care about.

## Overview

The system allows subscribers to choose:
- **Specific neighborhoods** (150+ available, e.g., "Fishtown", "Graduate Hospital")
- **Council districts** (Districts 1-10)
- **Multiple areas** (e.g., both Fishtown AND Northern Liberties)
- **Citywide** (receive all activity)

When a permit or variance is filed, subscribers only get emailed if it's in their selected area(s).

## How It Works

```
1. Daily: Fetch all permits/variances filed yesterday
2. Match each to its neighborhood using geographic boundaries
3. For each subscriber, filter to only their selected areas
4. Send personalized digest showing only relevant activity
```

**Example:**
- Subscriber chooses: Fishtown + Northern Liberties
- Yesterday's activity: 3 permits in Fishtown, 1 in Kensington, 2 in Old City
- Email sent: Only the 3 Fishtown permits (Kensington and Old City filtered out)

If there's NO activity in their areas, no email is sent!

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` - API calls
- `shapely` - Geographic matching (point-in-polygon)

### Step 2: Download Geographic Data

```bash
python download_geodata.py
```

This downloads:
- **150+ Philadelphia neighborhoods** from OpenDataPhilly
- **Council district boundaries** from Philly CARTO
- Saves to `geodata/` folder

Output:
```
✓ Downloaded 158 neighborhoods
✓ Downloaded 10 council districts
✓ Setup complete! Geographic data ready for filtering.
```

### Step 3: Set Up Buttondown

1. **Create a Buttondown account**: https://buttondown.email
2. **Get your API key**: Settings → API → Copy your API key
3. **Set environment variable**:

```bash
export BUTTONDOWN_API_KEY='your-api-key-here'
```

Or add to your `.bashrc` / `.zshrc`:
```bash
echo 'export BUTTONDOWN_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Configure Subscriber Preferences

Subscribers' geographic preferences are stored in Buttondown's subscriber metadata as JSON.

**Format:**
```json
{
  "neighborhoods": ["Fishtown", "Northern Liberties", "Kensington"],
  "districts": ["1", "5"],
  "frequency": "daily"
}
```

**How to set preferences:**

#### Option A: Via Buttondown Dashboard (Manual)
1. Go to Subscribers in Buttondown dashboard
2. Click on a subscriber
3. Add to "Metadata" field:
   ```json
   {"neighborhoods": ["Fishtown"], "frequency": "daily"}
   ```

#### Option B: Via Signup Form (Recommended)
Create a custom signup form with dropdowns:

```html
<form action="https://api.buttondown.email/v1/subscribers" method="post">
  <input type="hidden" name="api_key" value="YOUR_PUBLIC_KEY">

  <label>Email:</label>
  <input type="email" name="email" required>

  <label>Choose neighborhoods (hold Ctrl/Cmd for multiple):</label>
  <select name="metadata[neighborhoods]" multiple>
    <option value="Citywide">Citywide (All neighborhoods)</option>
    <option value="Fishtown">Fishtown</option>
    <option value="Northern Liberties">Northern Liberties</option>
    <option value="Kensington">Kensington</option>
    <!-- ... add all 150+ neighborhoods ... -->
  </select>

  <label>Or choose council districts:</label>
  <select name="metadata[districts]" multiple>
    <option value="1">District 1</option>
    <option value="2">District 2</option>
    <!-- ... -->
  </select>

  <label>Frequency:</label>
  <select name="metadata[frequency]">
    <option value="daily">Daily</option>
    <option value="weekly">Weekly</option>
  </select>

  <button type="submit">Subscribe</button>
</form>
```

#### Option C: Via API
```python
import requests

requests.post(
    'https://api.buttondown.email/v1/subscribers',
    headers={'Authorization': 'Token YOUR_API_KEY'},
    json={
        'email': 'user@example.com',
        'metadata': {
            'neighborhoods': ['Fishtown', 'Northern Liberties'],
            'frequency': 'daily'
        }
    }
)
```

### Step 5: Test the System

```bash
# Dry run - see what would be sent without actually sending
python send_daily_digests.py --dry-run

# Send for real
python send_daily_digests.py
```

## Available Neighborhoods

Run this to see all 150+ available neighborhoods:

```bash
python download_geodata.py
```

Sample neighborhoods:
- Fishtown
- Northern Liberties
- Kensington
- Graduate Hospital
- Rittenhouse Square
- University City
- Chestnut Hill
- Manayunk
- Old City
- ... and 140+ more!

## Automation with GitHub Actions

Add a daily workflow:

```yaml
# .github/workflows/daily-digest-geographic.yml
name: Send Daily Geographic Digests

on:
  schedule:
    - cron: '0 12 * * 1-5'  # Weekdays at 7 AM EST

jobs:
  send-digests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Download geographic data (cached)
        run: |
          if [ ! -d "geodata" ]; then
            python download_geodata.py
          fi

      - name: Send daily digests
        env:
          BUTTONDOWN_API_KEY: ${{ secrets.BUTTONDOWN_API_KEY }}
        run: python send_daily_digests.py
```

**Important:** Add `BUTTONDOWN_API_KEY` to GitHub Secrets:
1. Go to repo Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `BUTTONDOWN_API_KEY`
4. Value: your API key

## How Geographic Matching Works

The system uses **point-in-polygon matching**:

1. Each permit has coordinates: `geocode_x` and `geocode_y`
2. We load neighborhood boundaries as polygons from GeoJSON
3. For each permit, we check: "Is this point inside this polygon?"
4. Match found → assign neighborhood to permit

**Technical details:**
- Uses Shapely library for fast geometric operations
- Pre-processes polygons with `prep()` for 10x speed boost
- Quick bounding box check before detailed polygon test
- Handles edge cases (permits exactly on boundary, etc.)

## Subscriber Segmentation Examples

**Example 1: Citywide subscriber**
```json
{
  "frequency": "daily"
}
```
→ Receives ALL permits/variances daily

**Example 2: Single neighborhood**
```json
{
  "neighborhoods": ["Fishtown"],
  "frequency": "daily"
}
```
→ Only receives Fishtown activity

**Example 3: Multiple neighborhoods**
```json
{
  "neighborhoods": ["Fishtown", "Northern Liberties", "Kensington"],
  "frequency": "daily"
}
```
→ Receives activity from any of these 3 neighborhoods

**Example 4: Council district**
```json
{
  "districts": ["5"],
  "frequency": "daily"
}
```
→ Receives all activity in District 5

**Example 5: Mixed (neighborhood + district)**
```json
{
  "neighborhoods": ["Fishtown"],
  "districts": ["1"],
  "frequency": "daily"
}
```
→ Receives activity from Fishtown OR District 1

**Example 6: Weekly only**
```json
{
  "frequency": "weekly"
}
```
→ Skipped by daily digest, picked up by weekly digest instead

## Pricing Strategy

**Free tier:**
- Weekly citywide digest
- Good for casual readers

**Paid tier ($12-15/month):**
- Daily updates
- Geographic filtering
- Choose your neighborhoods
- Professional-grade intelligence

**Value proposition:**
"Know about every development in YOUR neighborhood the day it happens."

## Troubleshooting

### "No neighborhood matched"

Some permits may not have coordinates or coordinates may be invalid. These will show as:
```
neighborhood: None
```

They're still included in citywide digests and council district digests (using the `council_district` field from the permit data).

### "Coordinates seem wrong"

Philadelphia uses **State Plane coordinates** in the permit data, not lat/long. The system handles conversion automatically via Shapely.

If you see mismatches, check:
```python
python geographic_matcher.py
```

This runs test coordinates to verify the system is working.

### "Not enough activity in my neighborhood"

Some neighborhoods have very little development. Consider:
- Subscribing to multiple nearby neighborhoods
- Subscribing to your whole council district
- Subscribing citywide

You can always adjust preferences later!

### "Too many emails"

If a subscriber is getting too many emails:
1. Narrow their neighborhoods (fewer areas)
2. Switch them to weekly frequency
3. Increase min-units threshold (only show 3+ unit projects)

## Future Enhancements

Potential additions:
- **Custom polygons**: Draw your own area on a map
- **Radius filtering**: "Within 0.5 miles of my address"
- **Project size filtering**: Only 10+ unit projects
- **SMS alerts**: Text messages for major projects only
- **Digest summaries**: Weekly rollup even for daily subscribers

## Data Sources

- **Neighborhoods**: [OpenDataPhilly](https://opendataphilly.org/datasets/philadelphia-neighborhoods/) - 150+ neighborhood boundaries in GeoJSON format
- **Permits/Variances**: Philadelphia L&I Open Data via CARTO API
- **Council Districts**: Philadelphia CARTO (council_districts_2024 table)

---

**Questions?** Check the main [README.md](README.md) or [PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) for more context!
