# Philadelphia Development Digest - Quick Start Guide

## TL;DR

```bash
# Generate this week's digest
./run_digest.sh

# Or use Python directly
python3 generate_digest.py
```

Output will be saved to `digests/YYYY-MM-DD.md` - ready to paste into Substack!

## What You Get

**A weekly digest with:**
- **~12 by-right housing permits** (1+ units) - new rowhouses, duplexes, and small multi-family
- **~11 zoning variance applications** - with **multi-unit projects (5+) highlighted in bold**

**Organized by council district** for easy reading.

## Sample Week (Jan 6-13, 2026)

### By-Right Permits Found:
- 12 permits total
- Range: 1-3 units
- Largest: **3-unit** development at 2620 E HAROLD ST (District 1)
- Most active districts: Districts 1, 8, 5

### Zoning Variances with 5+ Units:
- **36 units** - 2401 N DOVER ST (District 5)
- **35 units** - 610-40 HIGH ST (District 8)
- **19 units** - 2416 N DOVER ST (District 5)
- **8 units** - 1946 N GRATZ ST (District 5)
- **8 units** - 1931 N 18TH ST (District 5)
- **7 units** - 329-31 FAIRMOUNT AVE (District 1)
- **5 units** - 1959 BRIDGE ST (District 7)
- **5 units** - 3807 GERMANTOWN AVE (District 8)

## Command Line Options

```bash
# Default: Last 7 days, 1+ units
./run_digest.sh

# Custom time period (last 14 days)
./run_digest.sh --days 14

# Change unit threshold (2+ units only)
./run_digest.sh --min-units 2

# Custom output directory
./run_digest.sh --output-dir weekly_reports
```

## Automation

The system is configured to run automatically every **Monday at 9 AM** via GitHub Actions. The digest will be:
1. Generated automatically
2. Saved to `digests/YYYY-MM-DD.md`
3. Committed and pushed to the repository

You can also trigger it manually from GitHub Actions if needed.

## Key Features

### 1. Smart Unit Extraction
The system extracts unit counts from both:
- The `numberofunits` database field (when available ~20% of the time)
- Project descriptions (using pattern matching)

**Patterns recognized:**
- "19 unit multi-family"
- "eight (8) dwelling units"
- "MULTIFAMILY"
- "five family household living"
- And many more variations!

### 2. Multi-Unit Highlighting
Variance applications with **5+ units** are automatically highlighted with bold unit counts:
```markdown
- **1946 N GRATZ ST** | **8 units**
```

This makes it easy to spot significant multi-family development.

### 3. Direct Links
Every permit includes a link to the Philadelphia L&I permit details page for easy verification and additional information.

## Understanding Philadelphia's Housing Development

Based on analysis of the data:

**By-Right Development (New Construction Permits):**
- Primarily 1-2 unit attached homes (rowhouses, duplexes)
- Weekly average: ~10-12 permits
- Occasionally 3-4 unit projects
- Rarely 5+ units (Philadelphia's zoning generally requires variances for larger projects)

**Zoning Variances:**
- Where most 5+ unit development happens
- Includes conversions, new construction in restricted zones, height/setback exceptions
- Weekly average: ~10-12 applications
- About 50-70% involve residential multi-unit development

**Most Active Districts:**
- District 5 (North Philadelphia) - Most variance applications
- District 8 (Germantown, Chestnut Hill, Mt. Airy)
- District 1 (South Philadelphia, Center City)

## Customization Ideas

Want to adjust the digest? Here are some options:

### Focus on Larger Projects Only
```bash
# Only show 3+ unit by-right permits
python3 generate_digest.py --min-units 3

# Only show 5+ unit projects
python3 generate_digest.py --min-units 5
```

### Monthly Roundup Instead of Weekly
```bash
# Last 30 days
python3 generate_digest.py --days 30
```

### Specific Date Range
Edit `generate_digest.py` and use custom start/end dates in the `generate_digest()` function.

## Troubleshooting

**"No permits found"**
- Try lowering the threshold: `--min-units 1`
- Expand time range: `--days 14` or `--days 30`

**API errors**
- Check your internet connection
- Verify CARTO API is accessible: https://phl.carto.com

**GitHub Actions not running**
- Check the Actions tab in your GitHub repository
- Ensure the workflow file is present in `.github/workflows/`
- Verify the schedule is correct (Monday 9 AM = 14:00 UTC)

## Files Overview

- **`generate_digest.py`** - Main digest generator (you can run this directly)
- **`run_digest.sh`** - Convenient wrapper script for easy execution
- **`analyze_descriptions.py`** - Tool to analyze unit extraction accuracy
- **`digests/`** - Output directory (created automatically)
- **`digest_sample_final.md`** - Example output

## Next Steps

1. ✅ Run your first digest: `./run_digest.sh`
2. ✅ Review the output in `digests/`
3. ✅ Paste into Substack and publish!
4. ✅ Customize the threshold/time period if needed
5. ✅ Let GitHub Actions handle weekly automation

---

**Questions?** Check the main [README.md](README.md) or review the analysis in [ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md).
