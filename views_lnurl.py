# Description: Extensions that use LNURL usually have a few endpoints in views_lnurl.py.

from http import HTTPStatus
from typing import Optional

import shortuuid
from fastapi import APIRouter, Query, Request
from lnbits.core.services import create_invoice, pay_invoice
from loguru import logger

from .crud import get_dca_admin

#################################################
########### A very simple LNURLpay ##############
# https://github.com/lnurl/luds/blob/luds/06.md #
#################################################
#################################################

dca_admin_lnurl_router = APIRouter()


@dca_admin_lnurl_router.get(
    "/api/v1/lnurl/pay/{dca_admin_id}",
    status_code=HTTPStatus.OK,
    name="dca_admin.api_lnurl_pay",
)
async def api_lnurl_pay(
    request: Request,
    dca_admin_id: str,
):
    dca_admin = await get_dca_admin(dca_admin_id)
    if not dca_admin:
        return {"status": "ERROR", "reason": "No dca_admin found"}
    return {
        "callback": str(
            request.url_for(
                "dca_admin.api_lnurl_pay_callback", dca_admin_id=dca_admin_id
            )
        ),
        "maxSendable": dca_admin.lnurlpayamount * 1000,
        "minSendable": dca_admin.lnurlpayamount * 1000,
        "metadata": '[["text/plain", "' + dca_admin.name + '"]]',
        "tag": "payRequest",
    }


@dca_admin_lnurl_router.get(
    "/api/v1/lnurl/paycb/{dca_admin_id}",
    status_code=HTTPStatus.OK,
    name="dca_admin.api_lnurl_pay_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    dca_admin_id: str,
    amount: int = Query(...),
):
    dca_admin = await get_dca_admin(dca_admin_id)
    logger.debug(dca_admin)
    if not dca_admin:
        return {"status": "ERROR", "reason": "No dca_admin found"}

    payment = await create_invoice(
        wallet_id=dca_admin.wallet,
        amount=int(amount / 1000),
        memo=dca_admin.name,
        unhashed_description=f'[["text/plain", "{dca_admin.name}"]]'.encode(),
        extra={
            "tag": "SatoshiMachine",
            "dca_adminId": dca_admin_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return {
        "pr": payment.bolt11,
        "routes": [],
        "successAction": {"tag": "message", "message": f"Paid {dca_admin.name}"},
    }


#################################################
######## A very simple LNURLwithdraw ############
# https://github.com/lnurl/luds/blob/luds/03.md #
#################################################
## withdraw is unlimited, look at withdraw ext ##
## for more advanced withdraw options          ##
#################################################


@dca_admin_lnurl_router.get(
    "/api/v1/lnurl/withdraw/{dca_admin_id}",
    status_code=HTTPStatus.OK,
    name="dca_admin.api_lnurl_withdraw",
)
async def api_lnurl_withdraw(
    request: Request,
    dca_admin_id: str,
):
    dca_admin = await get_dca_admin(dca_admin_id)
    if not dca_admin:
        return {"status": "ERROR", "reason": "No dca_admin found"}
    k1 = shortuuid.uuid(name=dca_admin.id)
    return {
        "tag": "withdrawRequest",
        "callback": str(
            request.url_for(
                "dca_admin.api_lnurl_withdraw_callback", dca_admin_id=dca_admin_id
            )
        ),
        "k1": k1,
        "defaultDescription": dca_admin.name,
        "maxWithdrawable": dca_admin.lnurlwithdrawamount * 1000,
        "minWithdrawable": dca_admin.lnurlwithdrawamount * 1000,
    }


@dca_admin_lnurl_router.get(
    "/api/v1/lnurl/withdrawcb/{dca_admin_id}",
    status_code=HTTPStatus.OK,
    name="dca_admin.api_lnurl_withdraw_callback",
)
async def api_lnurl_withdraw_cb(
    dca_admin_id: str,
    pr: Optional[str] = None,
    k1: Optional[str] = None,
):
    assert k1, "k1 is required"
    assert pr, "pr is required"
    dca_admin = await get_dca_admin(dca_admin_id)
    if not dca_admin:
        return {"status": "ERROR", "reason": "No dca_admin found"}

    k1_check = shortuuid.uuid(name=dca_admin.id)
    if k1_check != k1:
        return {"status": "ERROR", "reason": "Wrong k1 check provided"}

    await pay_invoice(
        wallet_id=dca_admin.wallet,
        payment_request=pr,
        max_sat=int(dca_admin.lnurlwithdrawamount * 1000),
        extra={
            "tag": "SatoshiMachine",
            "dca_adminId": dca_admin_id,
            "lnurlwithdraw": True,
        },
    )
    return {"status": "OK"}
