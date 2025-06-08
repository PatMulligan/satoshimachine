# Description: Add your page endpoints here.

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from lnbits.settings import settings

from .crud import get_satoshimachine
from .helpers import lnurler

satoshimachine_generic_router = APIRouter()


def satoshimachine_renderer():
    return template_renderer(["satoshimachine/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Backend admin page


@satoshimachine_generic_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return satoshimachine_renderer().TemplateResponse(
        "satoshimachine/index.html", {"request": req, "user": user.json()}
    )


# Frontend shareable page


@satoshimachine_generic_router.get("/{satoshimachine_id}")
async def satoshimachine(req: Request, satoshimachine_id):
    myex = await get_satoshimachine(satoshimachine_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )
    return satoshimachine_renderer().TemplateResponse(
        "satoshimachine/satoshimachine.html",
        {
            "request": req,
            "satoshimachine_id": satoshimachine_id,
            "lnurlpay": lnurler(myex.id, "satoshimachine.api_lnurl_pay", req),
            "web_manifest": f"/satoshimachine/manifest/{satoshimachine_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely


@satoshimachine_generic_router.get("/manifest/{satoshimachine_id}.webmanifest")
async def manifest(satoshimachine_id: str):
    satoshimachine = await get_satoshimachine(satoshimachine_id)
    if not satoshimachine:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )

    return {
        "short_name": settings.lnbits_site_title,
        "name": satoshimachine.name + " - " + settings.lnbits_site_title,
        "icons": [
            {
                "src": (
                    settings.lnbits_custom_logo
                    if settings.lnbits_custom_logo
                    else "https://cdn.jsdelivr.net/gh/lnbits/lnbits@0.3.0/docs/logos/lnbits.png"
                ),
                "type": "image/png",
                "sizes": "900x900",
            }
        ],
        "start_url": "/satoshimachine/" + satoshimachine_id,
        "background_color": "#1F2234",
        "description": "Minimal extension to build on",
        "display": "standalone",
        "scope": "/satoshimachine/" + satoshimachine_id,
        "theme_color": "#1F2234",
        "shortcuts": [
            {
                "name": satoshimachine.name + " - " + settings.lnbits_site_title,
                "short_name": satoshimachine.name,
                "description": satoshimachine.name + " - " + settings.lnbits_site_title,
                "url": "/satoshimachine/" + satoshimachine_id,
            }
        ],
    }
