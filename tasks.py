import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_satoshimachine, update_satoshimachine
from .models import CreateMyExtensionData

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_satoshimachine")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "MyExtension":
        return

    satoshimachine_id = payment.extra.get("satoshimachineId")
    assert satoshimachine_id, "satoshimachineId not set in invoice"
    satoshimachine = await get_satoshimachine(satoshimachine_id)
    assert satoshimachine, "MyExtension does not exist"

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = satoshimachine.total - payment.amount
    else:
        total = satoshimachine.total + payment.amount

    satoshimachine.total = total
    await update_satoshimachine(CreateMyExtensionData(**satoshimachine.dict()))

    # here we could send some data to a websocket on
    # wss://<your-lnbits>/api/v1/ws/<satoshimachine_id> and then listen to it on

    some_payment_data = {
        "name": satoshimachine.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(satoshimachine_id, str(some_payment_data))
