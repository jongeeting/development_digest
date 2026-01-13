# Philadelphia Development Digest - Analysis Summary

## Key Findings

### 1. Data Quality Issue: `numberofunits` Field Rarely Populated

- **Total residential permits in last 30 days:** 1,969
- **Permits with `numberofunits` populated:** 57 (less than 3%)
- **New construction permits:** Most have `numberofunits` filled
- **Other permit types:** Mostly missing unit counts

### 2. Actual Weekly Permit Volume (By-Right)

Analysis of last 30 days of new construction permits WITH unit counts:

| Threshold | Count (30 days) | Weekly Average |
|-----------|----------------|----------------|
| 1+ units  | 40 permits     | ~10 per week   |
| 2+ units  | 7 permits      | ~2 per week    |
| 3+ units  | 0 permits      | 0 per week     |
| 5+ units  | 0 permits      | 0 per week     |

**Reality Check:** Philadelphia's recent by-right housing is primarily **single-family attached homes** and **duplexes** (1-2 units). Very few 3+ unit projects are being built by-right.

### 3. Multi-Unit Housing is Happening Through ZONING VARIANCES

Looking at the last 30 days of zoning variance applications, we found **39 applications**, including:

**Large multi-unit projects requiring variances:**
- 2315-17 N 11TH ST: 20 dwelling units (District 5)
- 2416 N DOVER ST: 19 dwelling units (District 5)
- 1946 N GRATZ ST: 8 dwelling units (District 5)
- 1931 N 18TH ST: 8 dwelling units (District 5)
- 4045 SPRING GARDEN ST: 7 dwelling units (District 3)
- 1202 ALTER ST: 6 dwelling units (Unknown)
- 1959 BRIDGE ST: 5 dwelling units (District 7)
- 3807 GERMANTOWN AVE: 5 dwelling units (District 8)

**This is where your 5+ unit threshold makes sense - in the zoning variance applications, not by-right permits!**

### 4. Geographic Distribution

**Most active districts for new construction (1-2 units):**
- District 5: Most active (11 permits)
- District 8: Active (9 permits)
- District 1: Active (9 permits)

**Most active districts for zoning variances:**
- District 5: 10 applications
- District 1: 6 applications
- District 8: 4 applications

## Recommendations

### Option A: Focus on What's Actually Being Built By-Right
- **By-right permits:** Use 1-2+ unit threshold to capture actual rowhouse/townhouse development
- **Zoning variances:** All applications (most interesting ones are multi-unit anyway)
- **Weekly volume:** ~10-15 by-right permits + 5-10 variance applications

### Option B: Focus on Multi-Unit Development Only
- **By-right permits:** Use 5+ unit threshold (will be mostly empty most weeks)
- **Zoning variances:** Filter for 5+ unit projects only
- **Weekly volume:** 0-2 by-right permits + 1-3 variance applications
- **Pro:** More focused on significant multi-unit development
- **Con:** Misses the story of smaller-scale infill development

### Option C: Hybrid Approach (RECOMMENDED)
- **By-right permits:** Use 2+ unit threshold (captures duplexes and above)
- **Zoning variances:** Highlight multi-unit projects (5+ units) separately from other variances
- **Weekly volume:** ~2-3 by-right permits + full list of variances with multi-unit flagged
- **Pro:** Tells complete story of housing development
- **Con:** Slightly more work to categorize

## Data Quality Notes

1. **Neighborhoods:** The API doesn't return neighborhood names in the permits table. You may need to add a neighborhood lookup based on coordinates or addresses if you want neighborhood-level organization.

2. **"By-Right" Definition:** The term "by-right" typically means development that complies with zoning without needing variances. However, even 1-2 unit construction in Philadelphia often requires some zoning process. The cleanest definition for your digest might be:
   - **By-right section:** New construction residential building permits
   - **Variance section:** Zoning variance applications

3. **Zoning Board Appeals:** There are ~21 appeals per week total, but only about 10-12 are actually zoning variance applications for development. Many are appeals of violations, permit refusals, etc.

## Next Steps

1. **Decide on threshold:** Based on this analysis, I recommend 2+ units for by-right permits
2. **Test the digest:** Run weekly to see if the volume feels right
3. **Add neighborhoods:** If needed, we can add a neighborhood lookup
4. **Automation:** Set up GitHub Actions to run weekly

## Sample Outputs Generated

I've created sample digests with different thresholds:
- `sample_digest_1_units.md`: Shows all 1+ unit permits (40 permits)
- `sample_digest_5_units.md`: Shows only 5+ unit permits (0 permits)

Check these files to see what feels right for your audience!
