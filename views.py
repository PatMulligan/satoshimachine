# Description: Add your page endpoints here.

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from lnbits.settings import settings

from .crud import get_dca_admin, get_system_config
from .helpers import lnurler

dca_admin_generic_router = APIRouter()


def dca_admin_renderer():
    return template_renderer(["dca_admin/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Backend admin page


@dca_admin_generic_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/index.html", {"request": req, "user": user.json()}
    )


# Frontend shareable page


@dca_admin_generic_router.get("/{dca_admin_id}")
async def dca_admin(req: Request, dca_admin_id):
    myex = await get_dca_admin(dca_admin_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="SatoshiMachine does not exist."
        )
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/dca_admin.html",
        {
            "request": req,
            "dca_admin_id": dca_admin_id,
            "lnurlpay": lnurler(myex.id, "dca_admin.api_lnurl_pay", req),
            "web_manifest": f"/dca_admin/manifest/{dca_admin_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely


@dca_admin_generic_router.get("/manifest/{dca_admin_id}.webmanifest")
async def manifest(dca_admin_id: str):
    dca_admin = await get_dca_admin(dca_admin_id)
    if not dca_admin:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="SatoshiMachine does not exist."
        )

    return {
        "short_name": settings.lnbits_site_title,
        "name": dca_admin.name + " - " + settings.lnbits_site_title,
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
        "start_url": "/dca_admin/" + dca_admin_id,
        "background_color": "#1F2234",
        "description": "Minimal extension to build on",
        "display": "standalone",
        "scope": "/dca_admin/" + dca_admin_id,
        "theme_color": "#1F2234",
        "shortcuts": [
            {
                "name": dca_admin.name + " - " + settings.lnbits_site_title,
                "short_name": dca_admin.name,
                "description": dca_admin.name + " - " + settings.lnbits_site_title,
                "url": "/dca_admin/" + dca_admin_id,
            }
        ],
    }


# Description: DCA Admin Extension - Frontend Routes

dca_admin_router = APIRouter()


def dca_admin_renderer():
    return template_renderer(["dca_admin/templates"])


#######################################
##### DCA ADMIN PAGE ENDPOINTS #######
#######################################

# Main admin dashboard
@dca_admin_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/index.html", {"request": req, "user": user.json()}
    )

# Client management page
@dca_admin_router.get("/clients", response_class=HTMLResponse)
async def clients(req: Request, user: User = Depends(check_user_exists)):
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/clients.html", {"request": req, "user": user.json()}
    )

# Transaction monitoring page
@dca_admin_router.get("/transactions", response_class=HTMLResponse)
async def transactions(req: Request, user: User = Depends(check_user_exists)):
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/transactions.html", {"request": req, "user": user.json()}
    )

# Commission management page
@dca_admin_router.get("/commissions", response_class=HTMLResponse)
async def commissions(req: Request, user: User = Depends(check_user_exists)):
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/commissions.html", {"request": req, "user": user.json()}
    )

# System configuration page
@dca_admin_router.get("/settings", response_class=HTMLResponse)
async def settings(req: Request, user: User = Depends(check_user_exists)):
    config = await get_system_config()
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/settings.html", 
        {
            "request": req, 
            "user": user.json(),
            "config": config.dict() if config else {}
        }
    )

# Analytics dashboard
@dca_admin_router.get("/analytics", response_class=HTMLResponse)
async def analytics(req: Request, user: User = Depends(check_user_exists)):
    return dca_admin_renderer().TemplateResponse(
        "dca_admin/analytics.html", {"request": req, "user": user.json()}
    )
