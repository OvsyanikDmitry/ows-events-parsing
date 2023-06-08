""" API """
from fastapi.responses import HTMLResponse

from fastapi import FastAPI, Request

from routers import api_router

from fastapi.templating import Jinja2Templates

app = FastAPI()

app.include_router(api_router)


assets = Jinja2Templates(directory="assets")


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return assets.TemplateResponse("index.html", {"request": request})
