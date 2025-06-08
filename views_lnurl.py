# Description: Extensions that use LNURL usually have a few endpoints in views_lnurl.py.

from http import HTTPStatus
from typing import Optional

import shortuuid
from fastapi import APIRouter, Query, Request
from lnbits.core.services import create_invoice, pay_invoice
from loguru import logger

from .crud import get_satoshimachine

#################################################
########### A very simple LNURLpay ##############
# https://github.com/lnurl/luds/blob/luds/06.md #
#################################################
#################################################

satoshimachine_lnurl_router = APIRouter()


@satoshimachine_lnurl_router.get(
    "/api/v1/lnurl/pay/{satoshimachine_id}",
    status_code=HTTPStatus.OK,
    name="satoshimachine.api_lnurl_pay",
)
async def api_lnurl_pay(
    request: Request,
    satoshimachine_id: str,
):
    satoshimachine = await get_satoshimachine(satoshimachine_id)
    if not satoshimachine:
        return {"status": "ERROR", "reason": "No satoshimachine found"}
    return {
        "callback": str(
            request.url_for(
                "satoshimachine.api_lnurl_pay_callback", satoshimachine_id=satoshimachine_id
            )
        ),
        "maxSendable": satoshimachine.lnurlpayamount * 1000,
        "minSendable": satoshimachine.lnurlpayamount * 1000,
        "metadata": '[["text/plain", "' + satoshimachine.name + '"]]',
        "tag": "payRequest",
    }


@satoshimachine_lnurl_router.get(
    "/api/v1/lnurl/paycb/{satoshimachine_id}",
    status_code=HTTPStatus.OK,
    name="satoshimachine.api_lnurl_pay_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    satoshimachine_id: str,
    amount: int = Query(...),
):
    satoshimachine = await get_satoshimachine(satoshimachine_id)
    logger.debug(satoshimachine)
    if not satoshimachine:
        return {"status": "ERROR", "reason": "No satoshimachine found"}

    payment = await create_invoice(
        wallet_id=satoshimachine.wallet,
        amount=int(amount / 1000),
        memo=satoshimachine.name,
        unhashed_description=f'[["text/plain", "{satoshimachine.name}"]]'.encode(),
        extra={
            "tag": "SatoshiMachine",
            "satoshimachineId": satoshimachine_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return {
        "pr": payment.bolt11,
        "routes": [],
        "successAction": {"tag": "message", "message": f"Paid {satoshimachine.name}"},
    }


#################################################
######## A very simple LNURLwithdraw ############
# https://github.com/lnurl/luds/blob/luds/03.md #
#################################################
## withdraw is unlimited, look at withdraw ext ##
## for more advanced withdraw options          ##
#################################################


@satoshimachine_lnurl_router.get(
    "/api/v1/lnurl/withdraw/{satoshimachine_id}",
    status_code=HTTPStatus.OK,
    name="satoshimachine.api_lnurl_withdraw",
)
async def api_lnurl_withdraw(
    request: Request,
    satoshimachine_id: str,
):
    satoshimachine = await get_satoshimachine(satoshimachine_id)
    if not satoshimachine:
        return {"status": "ERROR", "reason": "No satoshimachine found"}
    k1 = shortuuid.uuid(name=satoshimachine.id)
    return {
        "tag": "withdrawRequest",
        "callback": str(
            request.url_for(
                "satoshimachine.api_lnurl_withdraw_callback", satoshimachine_id=satoshimachine_id
            )
        ),
        "k1": k1,
        "defaultDescription": satoshimachine.name,
        "maxWithdrawable": satoshimachine.lnurlwithdrawamount * 1000,
        "minWithdrawable": satoshimachine.lnurlwithdrawamount * 1000,
    }


@satoshimachine_lnurl_router.get(
    "/api/v1/lnurl/withdrawcb/{satoshimachine_id}",
    status_code=HTTPStatus.OK,
    name="satoshimachine.api_lnurl_withdraw_callback",
)
async def api_lnurl_withdraw_cb(
    satoshimachine_id: str,
    pr: Optional[str] = None,
    k1: Optional[str] = None,
):
    assert k1, "k1 is required"
    assert pr, "pr is required"
    satoshimachine = await get_satoshimachine(satoshimachine_id)
    if not satoshimachine:
        return {"status": "ERROR", "reason": "No satoshimachine found"}

    k1_check = shortuuid.uuid(name=satoshimachine.id)
    if k1_check != k1:
        return {"status": "ERROR", "reason": "Wrong k1 check provided"}

    await pay_invoice(
        wallet_id=satoshimachine.wallet,
        payment_request=pr,
        max_sat=int(satoshimachine.lnurlwithdrawamount * 1000),
        extra={
            "tag": "SatoshiMachine",
            "satoshimachineId": satoshimachine_id,
            "lnurlwithdraw": True,
        },
    )
    return {"status": "OK"}
