# Philadelphia Development Digest

Automated weekly digest of Philadelphia housing development activity, tracking:
- By-right housing permits (new construction)
- Zoning variance applications

Data sourced from the City of Philadelphia's Open Data portal via the CARTO API.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Generate a Digest

```bash
# Generate digest for the last 7 days (default)
python3 generate_digest.py

# Customize the time period and unit threshold
python3 generate_digest.py --days 14 --min-units 3

# Save to a file
python3 generate_digest.py --output digest.md

# Full example: 30 days, 2+ units, save to file
python3 generate_digest.py --days 30 --min-units 2 --output digest_$(date +%Y-%m-%d).md
```

### Command Line Options

- `--days N`: Number of days to look back (default: 7)
- `--min-units N`: Minimum number of units for by-right permits (default: 5)
- `--output FILE`: Save output to file instead of printing to console

## Understanding the Data

### What's a "By-Right" Permit?

In this digest, "by-right" refers to **new construction residential building permits** - projects that have received building permits without needing major zoning variances. These are typically:
- Single-family attached homes (rowhouses/townhouses)
- Small multi-family buildings (duplexes, triplexes)
- Occasionally larger projects in appropriately-zoned areas

### What's a Zoning Variance?

Zoning variance applications are requests to deviate from the zoning code. These often include:
- Multi-unit development in areas not zoned for it
- Buildings exceeding height limits
- Lot line adjustments
- Mixed-use developments
- Conversions of existing buildings to residential use

**Important:** Many of the largest multi-unit housing projects (5+ units) appear in the variance section, not the by-right section!

## Choosing the Right Unit Threshold

Based on analysis of Philadelphia's permit data:

| Threshold | Weekly Average | Best For |
|-----------|----------------|----------|
| 1+ units  | ~10 permits    | Comprehensive coverage of all residential construction |
| 2+ units  | ~2 permits     | Focus on duplexes and larger, filter out single-family |
| 3+ units  | ~0 permits     | Very few projects meet this threshold by-right |
| 5+ units  | ~0 permits     | Multi-unit at this scale usually requires variances |

**Recommendation:** Use `--min-units 2` to capture meaningful multi-family development while keeping the digest concise.

## Data Sources

- **Permits:** [Philadelphia L&I Building & Zoning Permits](https://opendataphilly.org/datasets/licenses-and-inspections-building-and-zoning-permits/)
- **Appeals:** [Philadelphia L&I Appeals](https://opendataphilly.org/datasets/licenses-and-inspections-appeals-of-code-violations-and-permit-refusals/)
- **API:** [Philadelphia CARTO API](https://phl.carto.com/api/v2/sql)

## Project Structure

```
development_digest/
├── generate_digest.py          # Main digest generator script
├── explore_api.py              # API exploration tool
├── analyze_volume.py           # Volume analysis tool
├── investigate_units.py        # Unit field investigation
├── find_multiunit_strategy.py  # Multi-unit identification strategy
├── requirements.txt            # Python dependencies
├── ANALYSIS_SUMMARY.md         # Detailed analysis of permit data
└── README.md                   # This file
```

## Automation

### GitHub Actions (Recommended)

A GitHub Actions workflow will run automatically every Monday to generate the digest. The workflow will:
1. Pull the latest permit and variance data
2. Generate the digest for the past 7 days
3. Save as `digests/YYYY-MM-DD.md`
4. Commit and push to the repository

See `.github/workflows/weekly-digest.yml` for configuration.

### Manual Scheduling

You can also use cron to run the digest on a schedule:

```bash
# Edit crontab
crontab -e

# Run every Monday at 9 AM
0 9 * * 1 cd /path/to/development_digest && python3 generate_digest.py --output digests/$(date +\%Y-\%m-\%d).md
```

## Analysis Tools

Several analysis scripts are included to help understand the data:

- `explore_api.py`: Explore available API fields and data structure
- `analyze_volume.py`: Analyze permit volumes at different thresholds
- `investigate_units.py`: Investigate data quality of the `numberofunits` field
- `find_multiunit_strategy.py`: Test strategies for identifying multi-unit permits

## Troubleshooting

### No Permits Found

If you're seeing "No permits found":
- Try lowering `--min-units` (try 2 or 1)
- Extend the time period with `--days 30`
- Check the API is accessible: `curl "https://phl.carto.com/api/v2/sql?q=SELECT%20COUNT(*)%20FROM%20permits"`

### API Errors

If you're getting API errors:
- Check your internet connection
- Verify the CARTO API is up: https://phl.carto.com
- Try reducing the time period (fewer days = smaller query)

## Contributing

Contributions welcome! Areas for improvement:
- Add neighborhood lookup functionality
- Better parsing of variance request descriptions
- Email or social media posting integration
- Web dashboard for browsing historical digests

## License

MIT License - feel free to adapt for other cities!

## Contact

For questions about the data, contact Philadelphia L&I: ligisteam@phila.gov

## References

- [OpenDataPhilly](https://opendataphilly.org/)
- [Philadelphia L&I](https://www.phila.gov/departments/department-of-licenses-and-inspections/)
- [CARTO SQL API Documentation](https://carto.com/developers/sql-api/)
