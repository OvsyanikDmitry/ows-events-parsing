from fastapi import APIRouter

from root.standalone.scrapers.scraper_belgrad_consult_com import get_data
from root.standalone.scrapers.scraper_visityerevan import scrape_visityerevan
from root.standalone.scrapers.scraper_batumifun import run_batches

router = APIRouter(prefix="/standalone")


@router.get("/belgrad_consult_com")
async def get_events() -> dict:
    data = await get_data()
    return {
        "status": "success",
        "data": data,
    }

  
@router.get("/visityerevan")
async def get_visityerevan_events():
    """returns json with data from visityerevan"""
    data = await scrape_visityerevan()
    return {"status": "success", "data": data}

  
@router.get("/batumifun")
async def get_events_batumifun() -> dict:
    data = await run_batches()
    return {
        "status": "success",
        "data": data,
    }

