"""
Scrapes batumi.fun
Processes pages asynchronously in batches of BSIZE pages,
stops when encounters empty pages
"""

import aiohttp
import asyncio
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import re


BASE_URL = 'https://batumi.fun/events/list/'
BATCH_SIZE = 10
MAX_BATCH_NUM = 4

# Selectolax selectors
EVENT_SEL = "div.tribe-events-calendar-list__event-row"
TITLE_SEL = "h3.tribe-events-calendar-list__event-title"
DTTM_SEL = "time.tribe-events-calendar-list__event-datetime"
DESC_SEL = "div.tribe-events-calendar-list__event-description"
ADDR_SEL = "address.tribe-events-calendar-list__event-venue"
IMG_SEL = "div.tribe-events-calendar-list__event-featured-image-wrapper"


def parse_datetime(dttm_node):
    """Parses date and time from given node"""
    raw_date = dttm_node.attributes['datetime']
    match_date = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', raw_date)
    iso_date = None if match_date is None else match_date.group()
    
    raw_time = dttm_node.text(strip=True)
    search_time = re.search(r'[0-9]{2}:[0-9]{2}', raw_time)
    time = None if search_time is None else search_time.group()
    return iso_date, time


def scrape_event(event_node):
    """Event scraper"""
    # Collect nodes
    title_node = event_node.css_first(TITLE_SEL)
    url_node = title_node.css_first("a")
    dttm_node = event_node.css_first(DTTM_SEL)
    desc_node = event_node.css_first(DESC_SEL)
    addr_nodes = event_node.css_first(ADDR_SEL).css("span")
    img_node = event_node.css_first(IMG_SEL).css_first("img")

    # Serialize data
    addr = ", ".join([n.text(strip=True) for n in addr_nodes])
    date, time = parse_datetime(dttm_node)
    event = {
        "id": "work in progress...",
        "type": "parsed_v1",
        "parserName": "batumi.fun",
        "title": title_node.text(strip=True),
        "description": desc_node.text(strip=True),
        "date": date + " " + time,
        "durationInSeconds": None,
        "location": {
            "country": "Gergia",
            "city": "Batumi",
            "address": addr
        },
        "image": img_node.attrs["src"],
        "price": None,
        "timezone": {
            "timezoneName": "GET",
            "timezoneOffset": "UTC +4",
        },
        "url": url_node.attrs["href"]
    }
    return event


def scrape_page(html):
    """Page scraper"""
    page_events = []
    
    # Find all event nodes
    tree = HTMLParser(html)
    event_nodes = tree.css(EVENT_SEL)

    # Process each event
    for event_node in event_nodes:
        page_events.append(scrape_event(event_node))
    
    return page_events


async def handle_page(pnum):
    """Single page handler, gets html and parses it"""
    batch_events = []
    async with aiohttp.ClientSession() as se:
        async with se.get(urljoin(BASE_URL, f'page/{pnum}')) as resp:
            # print(resp.status)
            page_events = scrape_page(await resp.text())
            batch_events += page_events
    return batch_events


async def run_batches():
    """Run all batches until encountering empty pages"""
    done = False
    it = 0
    events = []
    while not done:
        # Determine range of pages in batch
        batch_start = it * BATCH_SIZE + 1
        batch_end = (it + 1) * BATCH_SIZE
        pn_range = range(batch_start, batch_end + 1)
        print(f"Scraping pages {batch_start}-{batch_end}")
        it += 1

        # Process batch of pages
        tasks = [asyncio.create_task(handle_page(pn)) for pn in pn_range]
        parsed_pages = await asyncio.gather(*tasks)
        
        # Done if no events, empty page or too many batches
        done = it >= MAX_BATCH_NUM or \
            any((not page for page in parsed_pages))

        # Clear data and save to main list
        page_events = [ev for page in parsed_pages for ev in page]
        events += page_events
    return events


if __name__ == "__main__":
    events = asyncio.run(run_batches())
    print(len(events))
