import feedparser
import requests
from ics import Calendar, Event
from bs4 import BeautifulSoup
from datetime import datetime
import re
from zoneinfo import ZoneInfo  # Python 3.9+
# If you're on Python < 3.9, use: from pytz import timezone

rss_url = 'https://www.concordia.ca/content/concordia/en/next-gen/4th-space/programming/RSSCAL/_jcr_content/content-main/grid_container_671899525/grid-container-parsys/events_list.xml'

# Fix SSL certificate issue by downloading with requests first
def get_feed_content():
    """Download RSS content using requests (handles SSL better than feedparser)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(rss_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading RSS: {e}")
        return None

# Get RSS content and parse with feedparser
rss_content = get_feed_content()
if not rss_content:
    print("❌ Failed to download RSS content")
    exit(1)

feed = feedparser.parse(rss_content)
print(f"📦 Feed has {len(feed.entries)} entries")

calendar = Calendar()

def parse_event_datetime(text):
    """
    Parse date and start/end times from strings like:
    "June 19, 2025, 4 p.m. - 6 p.m."
    Returns (start_datetime, end_datetime) in Montreal timezone
    """
    match = re.search(
       r'([A-Za-z]+ \d{1,2}, \d{4}),\s*(\d{1,2}(?::\d{2})?)\s*([ap])\.m\.\s*[–-]\s*(\d{1,2}(?::\d{2})?)\s*([ap])\.m\.',
       text
    )
    if not match:
        return None, None
    
    date_str, start_time, start_ampm, end_time, end_ampm = match.groups()
    
    # Add missing minutes
    if ':' not in start_time:
        start_time += ':00'
    if ':' not in end_time:
        end_time += ':00'
    
    start_str = f"{date_str} {start_time} {start_ampm.upper()}M"
    end_str = f"{date_str} {end_time} {end_ampm.upper()}M"
    
    # Parse as naive datetime first
    start_dt = datetime.strptime(start_str, "%B %d, %Y %I:%M %p")
    end_dt = datetime.strptime(end_str, "%B %d, %Y %I:%M %p")
    
    # Add Montreal timezone
    montreal_tz = ZoneInfo("America/Montreal")
    start_dt = start_dt.replace(tzinfo=montreal_tz)
    end_dt = end_dt.replace(tzinfo=montreal_tz)
    
    return start_dt, end_dt

# Process each event
for entry in feed.entries:
    soup = BeautifulSoup(entry.summary, 'html.parser')
    text = soup.get_text()
    start_dt, end_dt = parse_event_datetime(text)
    
    print(f"\n🔍 TEXT FOR '{entry.title}':\n{text}") # Added this line to print what it gets even if it doesnt parse nice
    if not start_dt or not end_dt:
        print(f"⚠️ Skipping event with unparseable date: {entry.title}")
        continue
    event = Event()
    event.name = entry.title
    event.description = text
    event.url = entry.link
    event.begin = start_dt
    event.end = end_dt
    calendar.events.add(event)

# Save ICS file
with open("4SP_CAL_RSS_Events.ics", "w") as f:
    f.writelines(calendar)