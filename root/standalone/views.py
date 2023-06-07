from fastapi import APIRouter

from root.standalone.scrapers.scraper_belgrad_consult_com import get_data
from root.standalone.scrapers.scraper_visityerevan import scrape_visityerevan

router = APIRouter(prefix="/standalone")


@router.get("/belgrad_consult_com")
async def get_events() -> dict:
    data = await get_data()
    return {
        "status": "success",
        "data": data,
    }

@router.get('/visityerevan')
async def get_visityerevan_events():
    """ returns json with data from visityerevan """
    data = await scrape_visityerevan()
    return {
        "status": "success",
        "data": data
        }
