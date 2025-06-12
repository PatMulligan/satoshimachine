# Description: This file contains the extensions API endpoints.

from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, Request
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException

from .crud import (
    create_dca_admin,
    delete_dca_admin,
    get_dca_admin,
    get_dca_admins,
    update_dca_admin,
    create_dca_client,
    get_dca_client,
    get_dca_clients,
    update_dca_client,
    delete_dca_client,
    create_commission_recipient,
    get_commission_recipients,
    update_commission_recipient,
    delete_commission_recipient,
    get_system_config,
    update_system_config,
    get_processed_transactions,
    get_dca_distributions,
    get_commission_distributions,
    get_dca_metrics,
    get_client_metrics,
)
from .helpers import lnurler
from .models import CreateSatoshiMachineData, CreatePayment, SatoshiMachine, CreateDCAClientData, DCAClient, CreateCommissionRecipientData, CommissionRecipient, UpdateSystemConfigData, SystemConfig, DCAMetrics, ClientMetrics

dca_admin_api_router = APIRouter()

# Note: we add the lnurl params to returns so the links
# are generated in the SatoshiMachine model in models.py

## Get all the records belonging to the user


@dca_admin_api_router.get("/api/v1/myex")
async def api_dca_admins(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    wallet: WalletTypeInfo = Depends(require_invoice_key),
) -> list[SatoshiMachine]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    wallet_ids = user.wallet_ids if user else []
    dca_admins = await get_dca_admins(wallet_ids)

    # Populate lnurlpay and lnurlwithdraw for each instance.
    # Without the lnurl stuff this wouldnt be needed.
    for myex in dca_admins:
        myex.lnurlpay = lnurler(myex.id, "dca_admin.api_lnurl_pay", req)
        myex.lnurlwithdraw = lnurler(myex.id, "dca_admin.api_lnurl_withdraw", req)

    return dca_admins


## Get a single record


@dca_admin_api_router.get(
    "/api/v1/myex/{dca_admin_id}",
    dependencies=[Depends(require_invoice_key)],
)
async def api_dca_admin(dca_admin_id: str, req: Request) -> SatoshiMachine:
    myex = await get_dca_admin(dca_admin_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="SatoshiMachine does not exist."
        )
    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "dca_admin.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "dca_admin.api_lnurl_withdraw", req)

    return myex


## Create a new record


@dca_admin_api_router.post("/api/v1/myex", status_code=HTTPStatus.CREATED)
async def api_dca_admin_create(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreateSatoshiMachineData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> SatoshiMachine:
    myex = await create_dca_admin(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Withoutthe lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "dca_admin.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "dca_admin.api_lnurl_withdraw", req)

    return myex


## update a record


@dca_admin_api_router.put("/api/v1/myex/{dca_admin_id}")
async def api_dca_admin_update(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreateSatoshiMachineData,
    dca_admin_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> SatoshiMachine:
    myex = await get_dca_admin(dca_admin_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="SatoshiMachine does not exist."
        )

    if wallet.wallet.id != myex.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your SatoshiMachine."
        )

    for key, value in data.dict().items():
        setattr(myex, key, value)

    myex = await update_dca_admin(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "dca_admin.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "dca_admin.api_lnurl_withdraw", req)

    return myex


## Delete a record


@dca_admin_api_router.delete("/api/v1/myex/{dca_admin_id}")
async def api_dca_admin_delete(
    dca_admin_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    myex = await get_dca_admin(dca_admin_id)

    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="SatoshiMachine does not exist."
        )

    if myex.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your SatoshiMachine."
        )

    await delete_dca_admin(dca_admin_id)
    return


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@dca_admin_api_router.post("/api/v1/myex/payment", status_code=HTTPStatus.CREATED)
async def api_dca_admin_create_invoice(data: CreatePayment) -> dict:
    dca_admin = await get_dca_admin(data.dca_admin_id)

    if not dca_admin:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="SatoshiMachine does not exist."
        )

    # we create a payment and add some tags,
    # so tasks.py can grab the payment once its paid

    payment = await create_invoice(
        wallet_id=dca_admin.wallet,
        amount=data.amount,
        memo=(
            f"{data.memo} to {dca_admin.name}" if data.memo else f"{dca_admin.name}"
        ),
        extra={
            "tag": "dca_admin",
            "amount": data.amount,
        },
    )

    return {"payment_hash": payment.payment_hash, "payment_request": payment.bolt11}

dca_admin_api_router = APIRouter()

#######################################
##### DCA CLIENT ENDPOINTS ###########
#######################################

@dca_admin_api_router.get("/api/v1/clients")
async def api_get_clients(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> List[DCAClient]:
    """Get all DCA clients for the admin wallet."""
    return await get_dca_clients(wallet.wallet.id)

@dca_admin_api_router.get("/api/v1/clients/{client_id}")
async def api_get_client(
    client_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> DCAClient:
    """Get a specific DCA client."""
    client = await get_dca_client(client_id)
    if not client:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="DCA client not found."
        )
    return client

@dca_admin_api_router.post("/api/v1/clients", status_code=HTTPStatus.CREATED)
async def api_create_client(
    data: CreateDCAClientData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> DCAClient:
    """Create a new DCA client."""
    return await create_dca_client(data, wallet.wallet.id)

@dca_admin_api_router.put("/api/v1/clients/{client_id}")
async def api_update_client(
    client_id: str,
    data: CreateDCAClientData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> DCAClient:
    """Update a DCA client."""
    client = await get_dca_client(client_id)
    if not client:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="DCA client not found."
        )
    return await update_dca_client(client_id, data)

@dca_admin_api_router.delete("/api/v1/clients/{client_id}")
async def api_delete_client(
    client_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    """Delete a DCA client."""
    client = await get_dca_client(client_id)
    if not client:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="DCA client not found."
        )
    await delete_dca_client(client_id)

#######################################
##### COMMISSION RECIPIENT ENDPOINTS ##
#######################################

@dca_admin_api_router.get("/api/v1/commission-recipients")
async def api_get_commission_recipients(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> List[CommissionRecipient]:
    """Get all commission recipients."""
    return await get_commission_recipients(wallet.wallet.id)

@dca_admin_api_router.post("/api/v1/commission-recipients", status_code=HTTPStatus.CREATED)
async def api_create_commission_recipient(
    data: CreateCommissionRecipientData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> CommissionRecipient:
    """Create a new commission recipient."""
    return await create_commission_recipient(data, wallet.wallet.id)

@dca_admin_api_router.put("/api/v1/commission-recipients/{recipient_id}")
async def api_update_commission_recipient(
    recipient_id: str,
    data: CreateCommissionRecipientData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> CommissionRecipient:
    """Update a commission recipient."""
    return await update_commission_recipient(recipient_id, data)

@dca_admin_api_router.delete("/api/v1/commission-recipients/{recipient_id}")
async def api_delete_commission_recipient(
    recipient_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
):
    """Delete a commission recipient."""
    await delete_commission_recipient(recipient_id)

#######################################
##### SYSTEM CONFIG ENDPOINTS ########
#######################################

@dca_admin_api_router.get("/api/v1/config")
async def api_get_config(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> SystemConfig:
    """Get system configuration."""
    config = await get_system_config()
    if not config:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="System configuration not found."
        )
    return config

@dca_admin_api_router.put("/api/v1/config")
async def api_update_config(
    data: UpdateSystemConfigData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> SystemConfig:
    """Update system configuration."""
    return await update_system_config(data)

#######################################
##### TRANSACTION ENDPOINTS ##########
#######################################

@dca_admin_api_router.get("/api/v1/transactions")
async def api_get_transactions(
    wallet: WalletTypeInfo = Depends(require_admin_key),
    limit: int = 100,
    offset: int = 0,
):
    """Get processed transactions."""
    return await get_processed_transactions(wallet.wallet.id, limit, offset)

@dca_admin_api_router.get("/api/v1/distributions")
async def api_get_distributions(
    wallet: WalletTypeInfo = Depends(require_admin_key),
    limit: int = 100,
    offset: int = 0,
):
    """Get DCA distributions."""
    return await get_dca_distributions(wallet.wallet.id, limit, offset)

@dca_admin_api_router.get("/api/v1/commission-distributions")
async def api_get_commission_distributions(
    wallet: WalletTypeInfo = Depends(require_admin_key),
    limit: int = 100,
    offset: int = 0,
):
    """Get commission distributions."""
    return await get_commission_distributions(wallet.wallet.id, limit, offset)

#######################################
##### ANALYTICS ENDPOINTS ############
#######################################

@dca_admin_api_router.get("/api/v1/metrics")
async def api_get_metrics(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> DCAMetrics:
    """Get system-wide DCA metrics."""
    return await get_dca_metrics(wallet.wallet.id)

@dca_admin_api_router.get("/api/v1/clients/{client_id}/metrics")
async def api_get_client_metrics(
    client_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> ClientMetrics:
    """Get metrics for a specific client."""
    return await get_client_metrics(client_id)
