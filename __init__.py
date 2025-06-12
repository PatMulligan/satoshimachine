import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import dca_admin_generic_router
from .views_api import dca_admin_api_router
from .views_lnurl import dca_admin_lnurl_router

logger.debug(
    "This logged message is from dca_admin/__init__.py, you can debug in your "
    "extension using 'import logger from loguru' and 'logger.debug(<thing-to-log>)'."
)


dca_admin_ext: APIRouter = APIRouter(prefix="/dca_admin", tags=["SatoshiMachine"])
dca_admin_ext.include_router(dca_admin_generic_router)
dca_admin_ext.include_router(dca_admin_api_router)
dca_admin_ext.include_router(dca_admin_lnurl_router)

dca_admin_static_files = [
    {
        "path": "/dca_admin/static",
        "name": "dca_admin_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def dca_admin_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def dca_admin_start():
    task = create_permanent_unique_task("ext_dca_admin", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "dca_admin_ext",
    "dca_admin_static_files",
    "dca_admin_start",
    "dca_admin_stop",
]
