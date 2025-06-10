#!/usr/bin/env python3
"""
Automated RSS to ICS Calendar Generator
Run this script on a schedule (cron/Task Scheduler) to keep calendar updated
"""

import feedparser
import requests
from ics import Calendar, Event
from bs4 import BeautifulSoup
from datetime import datetime
import re
from zoneinfo import ZoneInfo
import os
import logging
from pathlib import Path

# Configuration
RSS_URL = 'https://www.concordia.ca/content/concordia/en/next-gen/4th-space/programming/RSSCAL/_jcr_content/content-main/grid_container_671899525/grid-container-parsys/events_list.xml'
OUTPUT_FILE = '4SP_CAL_RSS_Events.ics'
LOG_FILE = 'calendar_update.log'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_feed_content():
    """Download RSS content using requests (handles SSL better than feedparser)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(RSS_URL, headers=headers, timeout=30)
        response.raise_for_status()
        logging.info(f"Successfully downloaded RSS feed ({len(response.content)} bytes)")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading RSS: {e}")
        return None

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
    
    try:
        # Parse as naive datetime first
        start_dt = datetime.strptime(start_str, "%B %d, %Y %I:%M %p")
        end_dt = datetime.strptime(end_str, "%B %d, %Y %I:%M %p")
        
        # Add Montreal timezone
        montreal_tz = ZoneInfo("America/Montreal")
        start_dt = start_dt.replace(tzinfo=montreal_tz)
        end_dt = end_dt.replace(tzinfo=montreal_tz)
        
        return start_dt, end_dt
    except ValueError as e:
        logging.warning(f"Error parsing datetime: {e}")
        return None, None

def generate_calendar():
    """Generate ICS calendar from RSS feed"""
    # Get RSS content and parse with feedparser
    rss_content = get_feed_content()
    if not rss_content:
        logging.error("Failed to download RSS content")
        return False

    feed = feedparser.parse(rss_content)
    logging.info(f"Feed parsed - {len(feed.entries)} entries found")

    calendar = Calendar()
    events_processed = 0
    events_skipped = 0

    # Process each event
    for entry in feed.entries:
        try:
            soup = BeautifulSoup(entry.summary, 'html.parser')
            text = soup.get_text()
            start_dt, end_dt = parse_event_datetime(text)
            
            if not start_dt or not end_dt:
                logging.warning(f"Skipping event with unparseable date: {entry.title}")
                events_skipped += 1
                continue
                
            event = Event()
            event.name = entry.title
            event.description = text
            event.url = entry.link
            event.begin = start_dt
            event.end = end_dt
            calendar.events.add(event)
            events_processed += 1
            
        except Exception as e:
            logging.error(f"Error processing entry '{entry.title}': {e}")
            events_skipped += 1

    # Save ICS file
    try:
        with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
            f.writelines(calendar)
        logging.info(f"Calendar saved: {events_processed} events processed, {events_skipped} skipped")
        return True
    except Exception as e:
        logging.error(f"Error saving calendar: {e}")
        return False

def upload_to_server(file_path):
    """
    Upload ICS file to web server (customize this for your hosting)
    Examples for different hosting options:
    """
    
    # Example 1: Upload via FTP
    # import ftplib
    # try:
    #     ftp = ftplib.FTP('your-server.com')
    #     ftp.login('username', 'password')
    #     with open(file_path, 'rb') as f:
    #         ftp.storbinary('STOR calendar.ics', f)
    #     ftp.quit()
    #     logging.info("File uploaded via FTP")
    #     return True
    # except Exception as e:
    #     logging.error(f"FTP upload failed: {e}")
    #     return False
    
    # Example 2: Upload to cloud storage (AWS S3, Google Cloud, etc.)
    # This would require additional libraries and setup
    
    # Example 3: Copy to web server directory (if running on same server)
    # import shutil
    # try:
    #     shutil.copy(file_path, '/var/www/html/calendar.ics')
    #     logging.info("File copied to web directory")
    #     return True
    # except Exception as e:
    #     logging.error(f"File copy failed: {e}")
    #     return False
    
    logging.info("Upload function not configured - file saved locally only")
    return True

def main():
    """Main function"""
    logging.info("Starting calendar update process")
    
    # Generate calendar
    if generate_calendar():
        # Upload to server (customize upload_to_server function)
        upload_to_server(OUTPUT_FILE)
        logging.info("Calendar update completed successfully")
    else:
        logging.error("Calendar update failed")

if __name__ == "__main__":
    main()
