# GitHub Actions Setup - Automated Weekly Digest

This guide shows you how to set up and run the automated weekly digest using GitHub Actions.

## Overview

The workflow is already configured and will:
- **Run automatically every Monday at 9 AM EST**
- Generate a digest for the past 7 days
- Save it to `digests/YYYY-MM-DD.md`
- Commit and push the file to your repository

## Step 1: Merge the Branch (Optional but Recommended)

The code is currently on branch `claude/weekly-digest-automation-dMVH6`.

**To merge to main:**

1. Go to your repository: `https://github.com/jongeeting/development_digest`
2. Click **"Pull requests"** tab
3. Click **"New pull request"**
4. Select:
   - Base: `main`
   - Compare: `claude/weekly-digest-automation-dMVH6`
5. Click **"Create pull request"**
6. Add a title like "Add automated weekly digest system"
7. Click **"Create pull request"** again
8. Click **"Merge pull request"**
9. Click **"Confirm merge"**

**Or skip this step** and the workflow will run from the feature branch.

## Step 2: Enable GitHub Actions (if needed)

1. Go to your repository
2. Click **"Settings"** tab (top right)
3. Click **"Actions"** → **"General"** in the left sidebar
4. Make sure **"Allow all actions and reusable workflows"** is selected
5. Scroll down and click **"Save"** if you made changes

## Step 3: Run the Workflow Manually (Test It!)

1. **Navigate to your repository:**
   ```
   https://github.com/jongeeting/development_digest
   ```

2. **Click the "Actions" tab** at the top of the page

3. **Find the workflow:**
   - Look in the left sidebar
   - Click **"Generate Weekly Digest"**

4. **Run it manually:**
   - Look for the **"Run workflow"** dropdown button (top right area)
   - Click it to expand the dropdown
   - Select branch:
     - `claude/weekly-digest-automation-dMVH6` (if you didn't merge)
     - OR `main` (if you merged)
   - You'll see optional parameters:
     - **Days**: Leave as `7` (default)
     - **Min units**: Leave as `2` (default)
   - Click the green **"Run workflow"** button

5. **Watch it run:**
   - Wait 5-10 seconds, then **refresh the page**
   - You'll see a new workflow run appear
   - Yellow dot 🟡 = currently running
   - Green checkmark ✅ = success
   - Red X ❌ = failed (see logs for details)
   - Click on the workflow run to see real-time logs

## Step 4: Find Your Generated Digest

After the workflow completes successfully:

1. **Go back to your repository's main page:**
   - Click **"Code"** tab
   - OR click on `<> Code` at the top

2. **Find the digest:**
   - You should see a new folder: **`digests/`**
   - Click on it
   - You'll see a file named `YYYY-MM-DD.md` (today's date)

3. **View the digest:**
   - Click on the markdown file
   - GitHub will render it nicely
   - Click the **"Raw"** button (top right) to see the plain text

4. **Copy to Substack:**
   - Click the **"Copy raw file"** button (appears when you hover)
   - OR select all the text and copy it
   - Paste into Substack's editor

## Step 5: Sit Back and Relax!

From now on, the workflow will **run automatically every Monday at 9 AM EST**:

1. Check your repository on Monday afternoons
2. Look in the `digests/` folder for the new file
3. Copy the content and publish to Substack

That's it!

## Customizing the Weekly Run

If you want to change the schedule or default parameters:

1. **Go to** `.github/workflows/weekly-digest.yml` in your repository
2. **Click the pencil icon** (Edit this file)
3. **Change the schedule:**
   ```yaml
   schedule:
     - cron: '0 14 * * 1'  # Monday at 2 PM UTC (9 AM EST)
   ```
   - Change `'0 14 * * 1'` to your preferred time
   - Use [crontab.guru](https://crontab.guru/) to help build the cron expression
   - Remember: GitHub uses UTC time

4. **Change default parameters:**
   ```yaml
   DAYS="${{ github.event.inputs.days || '7' }}"
   MIN_UNITS="${{ github.event.inputs.min_units || '2' }}"
   ```
   - Change `'7'` to look back more/fewer days
   - Change `'2'` to adjust the minimum unit threshold

5. **Commit the changes**

## Troubleshooting

### Workflow doesn't appear in Actions tab

**Check:**
- Make sure you're on the correct branch
- Verify `.github/workflows/weekly-digest.yml` exists
- Confirm GitHub Actions is enabled (Settings → Actions)

### Workflow fails with error

**Common issues:**
1. **API error**: The CARTO API might be temporarily down - retry later
2. **Permission error**: Make sure GitHub Actions has write permissions
   - Go to Settings → Actions → General
   - Scroll to "Workflow permissions"
   - Select "Read and write permissions"
   - Click Save

### No digest file appears after successful run

**Check:**
1. Look in the `digests/` folder in the **correct branch**
2. Check the workflow logs - did it actually create the file?
3. Try pulling the latest changes if viewing locally: `git pull`

### Want to test with different parameters

Run the workflow manually and change the inputs:
- **Days**: Try `14` or `30` for a longer period
- **Min units**: Try `1` to see all permits, or `5` to see only large projects

## Need Help?

If you run into issues:

1. Check the **Actions** tab and look at the logs from failed runs
2. Make sure all files were committed and pushed properly
3. Verify the branch you're working on has the workflow file

The workflow should just work! Once you've tested it manually and seen it succeed, you can trust it to run automatically every Monday.

---

**Next:** Check out [QUICK_START.md](QUICK_START.md) if you want to run digests locally instead!
