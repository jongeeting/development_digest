# Build Philly Now - Email Integration Setup

## Current Status

The system is ready for **Phase 1: Weekly Citywide Digests**

## Phase 1: Substack Weekly Digest (NOW)

### How It Works

1. **GitHub Actions runs every Monday at 9 AM**
2. Generates weekly digest (markdown format)
3. Saves to `digests/YYYY-MM-DD.md`
4. You copy/paste into Substack and send

**That's it!** Simple, automated content generation.

### Setup Steps

1. ✅ Code is ready (already done)
2. ✅ GitHub Actions configured (already done)
3. **TODO:** Test the weekly workflow
4. **TODO:** Create Substack publication

### To Generate a Digest Now

```bash
# Generate this week's digest
python3 generate_digest.py

# Or for a specific time period
python3 generate_digest.py --days 7 --min-units 1
```

Output is ready to paste into Substack!

---

## Phase 2: Buttondown Integration (3-6 months)

**When you're ready** to add daily/geographic alerts, everything is built and ready.

### What's Already Built

✅ Geographic matching (150+ Philly neighborhoods)
✅ Buttondown API integration
✅ Subscriber filtering by neighborhood/district
✅ Daily digest generator
✅ Full documentation

### Your Buttondown Account

You have a Buttondown account with an API key (expires 2025-06-01).

⚠️ **IMPORTANT:** Never commit your API key to git.

### When You're Ready to Launch Phase 2

1. **Set up your environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Buttondown API key
   ```

2. **Load the environment variable:**
   ```bash
   source .env
   # Or add to your ~/.bashrc or ~/.zshrc
   ```

3. **Download geographic data:**
   ```bash
   python3 download_geodata.py
   ```

4. **Test the system:**
   ```bash
   python3 send_daily_digests.py --dry-run
   ```

5. **Go live:**
   ```bash
   python3 send_daily_digests.py
   ```

### GitHub Actions Secret

When you want to automate daily sends:

1. Go to your repo: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `BUTTONDOWN_API_KEY`
4. Value: Your Buttondown API key
5. Save

Then GitHub Actions can send emails automatically.

---

## Phase 3: Vercel Dashboard Integration (6-12 months)

**When Vercel is ready** to manage email preferences, you'll:

1. Add authentication to Vercel dashboard
2. Add "Email Preferences" page where users choose neighborhoods
3. Store preferences in your database
4. Vercel backend calls our Python scripts to send emails
5. One unified platform!

---

## Positioning for Build Philly Now

### Content Arm (Substack)
- Weekly development digest
- Meeting coverage and analysis
- Policy briefs and reports
- Opinion and ideas
- Freelance/student content

**Value:** Become the go-to intellectual voice on built environment policy

### Data Arm (Vercel Dashboard)
- Property data visualization
- Permit and zoning data (coming)
- Interactive maps and charts
- Eventually: API access for researchers/developers

**Value:** The data source for Philly development

### Alert Arm (Buttondown - Phase 2)
- Daily development updates
- Geographic filtering (your neighborhood only)
- Professional intelligence service

**Value:** Real-time competitive intelligence for professionals

---

## Recommended Pricing Strategy

### Free Tier
- Weekly Substack digest (citywide)
- Read-only Vercel dashboard
- Build audience, establish brand

### Supporter Tier ($10/month)
- Full Substack access (all reports, analysis, policy briefs)
- Enhanced Vercel dashboard (export data, better filters)
- Support the mission

### Professional Tier ($25/month) - Phase 2
- Everything in Supporter
- Daily geographic email alerts (via Buttondown)
- API access to data
- For real estate pros, planners, developers, policy orgs

### Institutional Tier ($100+/month) - Phase 3
- Everything in Professional
- White-label data products
- Custom research requests
- Priority support
- For advocacy orgs, trade associations, large developers

---

## Next Steps (Immediate)

1. **Test the weekly digest:**
   ```bash
   python3 generate_digest.py --output test_digest.md
   cat test_digest.md
   ```

2. **Set up your Substack:**
   - Create "Build Philly Now" publication
   - Create first post with the digest
   - Add free/paid tiers

3. **Let GitHub Actions run Monday** and generate your first automated digest

4. **Start building your Vercel dashboard** with basic property data

5. **Focus on content:** Meeting coverage, analysis, policy briefs

When you have 50+ paid Substack subscribers and they're asking for daily updates, **then** activate Phase 2 (Buttondown).

---

## Documentation

- **Phase 1 (Weekly):** Use existing `README.md` and `QUICK_START.md`
- **Phase 2 (Daily/Geographic):** See `GEOGRAPHIC_FILTERING_GUIDE.md`
- **GitHub Actions:** See `GITHUB_ACTIONS_SETUP.md`

Everything is built and ready. Just choose your pace!

---

## Build Philly Now Mission Alignment

This email system supports your goals:

**Think Tank + Data Broker:**
- Generate valuable policy-relevant data
- Make it accessible to professionals and researchers
- Establish Build Philly Now as the authority on development data

**Talent Development:**
- Data powers original research by freelancers and students
- Weekly digest showcases your analytical capabilities
- Attracts collaborators who value data-driven work

**Growth Coalition Support:**
- Real-time intelligence for builders and developers
- Transparency that benefits pro-development advocates
- Data that counters NIMBY narratives with facts

**Remember:** Focus on content first. The tech is ready when you need it.
