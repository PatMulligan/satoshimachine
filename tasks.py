import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_dca_admin, update_dca_admin
from .models import CreateSatoshiMachineData

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_dca_admin")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "SatoshiMachine":
        return

    dca_admin_id = payment.extra.get("dca_adminId")
    assert dca_admin_id, "dca_adminId not set in invoice"
    dca_admin = await get_dca_admin(dca_admin_id)
    assert dca_admin, "SatoshiMachine does not exist"

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = dca_admin.total - payment.amount
    else:
        total = dca_admin.total + payment.amount

    dca_admin.total = total
    await update_dca_admin(CreateSatoshiMachineData(**dca_admin.dict()))

    # here we could send some data to a websocket on
    # wss://<your-lnbits>/api/v1/ws/<dca_admin_id> and then listen to it on

    some_payment_data = {
        "name": dca_admin.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(dca_admin_id, str(some_payment_data))
