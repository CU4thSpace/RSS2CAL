# 4th Space Events Calendar — How This Works

This repo automatically keeps an Outlook-subscribable calendar (`.ics` file) up to date with 4th Space events, using three pieces that work together:

## The three files

**`4SPEVENTSCAL.py`** (the script)
Downloads the 4th Space events RSS feed from the Concordia AEM CMS, reads each event's title, date/time, and link, and builds a calendar file from it. This is the file that actually does the work.

**`update-calendar.yml`** (the workflow, in `.github/workflows/`)
Tells GitHub to automatically run the Python script on a schedule (currently every 2 hours), and to save/commit the result back to the repo. You can also trigger it manually from the "Actions" tab on GitHub.

**`4SP_CAL_RSS_Events.ics`** (the calendar file)
The actual output — this is the file Outlook subscribes to. Every time the workflow runs the script, this file gets regenerated and pushed to GitHub. Outlook checks this file periodically (every 12–24 hours) and pulls in any changes automatically.

## How they connect

```
RSS Feed (Concordia website)
       ↓
4SPEVENTSCAL.py  ← runs automatically via update-calendar.yml
       ↓
4SP_CAL_RSS_Events.ics  (saved in GitHub)
       ↓
Outlook (subscribed to the GitHub-hosted .ics link)
```

No one needs to manually run anything day-to-day — the GitHub Action handles it on a timer.

## If you need to update the Python script

1. Open the repo on GitHub.
2. Open `4SPEVENTSCAL.py` and click the edit (pencil) icon.
3. Replace the content with the new version.
4. **Keep the filename exactly the same** (`4SPEVENTSCAL.py`) — the workflow file references it by name, so a mismatch will break the automation.
5. Commit the change directly to the main branch (or via a pull request, if that's your repo's process).
6. To see the update reflected right away instead of waiting for the next scheduled run:
   - Go to the **Actions** tab
   - Click **Update Calendar**
   - Click **Run workflow**
7. Check that the run succeeds (green checkmark). If it fails, click into the run to see the error log.
8. Outlook will pick up the new `.ics` content on its next automatic refresh — this isn't instant, so don't expect it to show up the second the workflow finishes.

## Quick troubleshooting

- **Workflow not running on schedule?** GitHub auto-disables scheduled runs after 60 days of no commits to the repo — just push any small change or run it manually to reactivate.
- **Push step failing?** Check that `permissions: contents: write` is still set in the YML file.
- **Script erroring in the log?** Usually means the RSS feed structure changed on Concordia's end, or a dependency needs updating.
