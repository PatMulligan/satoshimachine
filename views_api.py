# Description: This file contains the extensions API endpoints.

from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException

from .crud import (
    create_satoshimachine,
    delete_satoshimachine,
    get_satoshimachine,
    get_satoshimachines,
    update_satoshimachine,
)
from .helpers import lnurler
from .models import CreateMyExtensionData, CreatePayment, MyExtension

satoshimachine_api_router = APIRouter()

# Note: we add the lnurl params to returns so the links
# are generated in the MyExtension model in models.py

## Get all the records belonging to the user


@satoshimachine_api_router.get("/api/v1/myex")
async def api_satoshimachines(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    wallet: WalletTypeInfo = Depends(require_invoice_key),
) -> list[MyExtension]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    wallet_ids = user.wallet_ids if user else []
    satoshimachines = await get_satoshimachines(wallet_ids)

    # Populate lnurlpay and lnurlwithdraw for each instance.
    # Without the lnurl stuff this wouldnt be needed.
    for myex in satoshimachines:
        myex.lnurlpay = lnurler(myex.id, "satoshimachine.api_lnurl_pay", req)
        myex.lnurlwithdraw = lnurler(myex.id, "satoshimachine.api_lnurl_withdraw", req)

    return satoshimachines


## Get a single record


@satoshimachine_api_router.get(
    "/api/v1/myex/{satoshimachine_id}",
    dependencies=[Depends(require_invoice_key)],
)
async def api_satoshimachine(satoshimachine_id: str, req: Request) -> MyExtension:
    myex = await get_satoshimachine(satoshimachine_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )
    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "satoshimachine.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "satoshimachine.api_lnurl_withdraw", req)

    return myex


## Create a new record


@satoshimachine_api_router.post("/api/v1/myex", status_code=HTTPStatus.CREATED)
async def api_satoshimachine_create(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreateMyExtensionData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> MyExtension:
    myex = await create_satoshimachine(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Withoutthe lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "satoshimachine.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "satoshimachine.api_lnurl_withdraw", req)

    return myex


## update a record


@satoshimachine_api_router.put("/api/v1/myex/{satoshimachine_id}")
async def api_satoshimachine_update(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreateMyExtensionData,
    satoshimachine_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> MyExtension:
    myex = await get_satoshimachine(satoshimachine_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )

    if wallet.wallet.id != myex.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your MyExtension."
        )

    for key, value in data.dict().items():
        setattr(myex, key, value)

    myex = await update_satoshimachine(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "satoshimachine.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "satoshimachine.api_lnurl_withdraw", req)

    return myex


## Delete a record


@satoshimachine_api_router.delete("/api/v1/myex/{satoshimachine_id}")
async def api_satoshimachine_delete(
    satoshimachine_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    myex = await get_satoshimachine(satoshimachine_id)

    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )

    if myex.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your MyExtension."
        )

    await delete_satoshimachine(satoshimachine_id)
    return


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@satoshimachine_api_router.post("/api/v1/myex/payment", status_code=HTTPStatus.CREATED)
async def api_satoshimachine_create_invoice(data: CreatePayment) -> dict:
    satoshimachine = await get_satoshimachine(data.satoshimachine_id)

    if not satoshimachine:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="MyExtension does not exist."
        )

    # we create a payment and add some tags,
    # so tasks.py can grab the payment once its paid

    payment = await create_invoice(
        wallet_id=satoshimachine.wallet,
        amount=data.amount,
        memo=(
            f"{data.memo} to {satoshimachine.name}" if data.memo else f"{satoshimachine.name}"
        ),
        extra={
            "tag": "satoshimachine",
            "amount": data.amount,
        },
    )

    return {"payment_hash": payment.payment_hash, "payment_request": payment.bolt11}
