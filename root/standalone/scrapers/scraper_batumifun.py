"""
Scrapes batumi.fun
Processes pages asynchronously in batches of BSIZE pages,
stops when encounters empty pages
"""

import aiohttp
import asyncio
import logging
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from datetime import datetime
import re


BASE_URL = "https://batumi.fun/events/list/"
BATCH_SIZE = 10
MAX_BATCH_NUM = 4

# Selectolax selectors
NAVBAR_SEL = "tribe-events-header__top-bar"
EVENT_SEL = "div.tribe-events-calendar-list__event-row"
TITLE_SEL = "h3.tribe-events-calendar-list__event-title"
DTTM_SEL = "time.tribe-events-calendar-list__event-datetime"
DESC_SEL = "div.tribe-events-calendar-list__event-description"
ADDR_SEL = "address.tribe-events-calendar-list__event-venue"
IMG_SEL = "div.tribe-events-calendar-list__event-featured-image-wrapper"
PRICE_SEL = "span.tribe-events-c-small-cta__price"


# Uncomment to see debug messages
# logging.basicConfig(level=logging.DEBUG)


def warn_outdated(field):
    logging.warning(f"Failed to scrape {field}, parser might be outdated.")


def is_valid(node, field):
    if node is None:
        warn_outdated(field)
        return False
    else:
        return True


def parse_datetime(dttm_node):
    """Parses date and time from given node"""
    raw_time = dttm_node.text(strip=True)
    search_time = re.search(r"[0-9]{2}:[0-9]{2}", raw_time)
    if not search_time:
        warn_outdated("Time")
        time_str = "00:00"
    else:
        time_str = search_time.group()

    try:
        iso_date = dttm_node.attributes["datetime"]
        dttm_str = f"{iso_date} {time_str}"
        dttm = datetime.strptime(dttm_str, "%Y-%m-%d %H:%M")
    except (ValueError, KeyError):
        warn_outdated("Date")
        dttm = 0
    return dttm.timestamp()


def scrape_event(event_node):
    """Event scraper"""
    # Collect nodes
    title_node = event_node.css_first(TITLE_SEL)
    if is_valid(title_node, "Title"):
        title = title_node.text(strip=True)
    else:
        title = None

    url_node = title_node.css_first("a")
    if is_valid(url_node, "URL"):
        url = url_node.attrs["href"]
    else:
        url = None

    dttm_node = event_node.css_first(DTTM_SEL)
    if is_valid(dttm_node, "Date and time"):
        timestamp = parse_datetime(dttm_node)
    else:
        timestamp = None

    desc_node = event_node.css_first(DESC_SEL)
    if is_valid(desc_node, "Description"):
        description = desc_node.text(strip=True)
    else:
        description = None

    addr_nodes = event_node.css_first(ADDR_SEL).css("span")
    if is_valid(addr_nodes, "Address"):
        addr = ", ".join([n.text(strip=True) for n in addr_nodes])
    else:
        addr = None

    img_node = event_node.css_first(IMG_SEL).css_first("img")
    if is_valid(img_node, "Image"):
        img = img_node.attrs["src"]
    else:
        img = None

    price_node = event_node.css_first(PRICE_SEL)
    # Price block may be absent
    if price_node is not None:
        price = price_node.text(strip=True).replace("₾", "")
    else:
        price = None

    # Serialize data
    event = {
        "id": "work in progress...",
        "type": "parsed_v1",
        "parserName": "batumi.fun",
        "title": title,
        "description": description,
        "date": timestamp,
        "durationInSeconds": None,
        "location": {"country": "Gergia", "city": "Batumi", "address": addr},
        "image": img,
        "price": price,
        "timezone": {
            "timezoneName": "Asia/Tbilisi",
            "timezoneOffset": "+ 04:00",
        },
        "url": url,
    }
    return event


def scrape_page(html):
    """Page scraper"""
    page_events = []
    tree = HTMLParser(html)

    # Try to scrape navigation bar first to make sure script is up-to-date
    navbar_node = tree.css(NAVBAR_SEL)
    if navbar_node is None:
        warn_outdated("Navigation bar")
        return []
    event_nodes = tree.css(EVENT_SEL)

    # Process each event
    for event_node in event_nodes:
        page_events.append(scrape_event(event_node))

    return page_events


async def handle_page(pnum):
    """Single page handler, gets html and parses it"""
    batch_events = []
    async with aiohttp.ClientSession() as se:
        async with se.get(urljoin(BASE_URL, f"page/{pnum}")) as resp:
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
        logging.debug(f"Scraping pages {batch_start}-{batch_end}")
        it += 1

        # Process batch of pages
        tasks = [asyncio.create_task(handle_page(pn)) for pn in pn_range]
        parsed_pages = await asyncio.gather(*tasks)

        # Done if no events, empty page or too many batches
        done = it >= MAX_BATCH_NUM or any((not page for page in parsed_pages))
        if done:
            logging.debug("Encountered empty page, finishing")

        # Clear data and save to main list
        page_events = [ev for page in parsed_pages for ev in page]
        events += page_events
    return events


if __name__ == "__main__":
    events = asyncio.run(run_batches())
    print(events)
