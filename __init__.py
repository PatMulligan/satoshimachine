import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import satoshimachine_generic_router
from .views_api import satoshimachine_api_router
from .views_lnurl import satoshimachine_lnurl_router

logger.debug(
    "This logged message is from satoshimachine/__init__.py, you can debug in your "
    "extension using 'import logger from loguru' and 'logger.debug(<thing-to-log>)'."
)


satoshimachine_ext: APIRouter = APIRouter(prefix="/satoshimachine", tags=["MyExtension"])
satoshimachine_ext.include_router(satoshimachine_generic_router)
satoshimachine_ext.include_router(satoshimachine_api_router)
satoshimachine_ext.include_router(satoshimachine_lnurl_router)

satoshimachine_static_files = [
    {
        "path": "/satoshimachine/static",
        "name": "satoshimachine_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def satoshimachine_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def satoshimachine_start():
    task = create_permanent_unique_task("ext_satoshimachine", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "satoshimachine_ext",
    "satoshimachine_static_files",
    "satoshimachine_start",
    "satoshimachine_stop",
]
