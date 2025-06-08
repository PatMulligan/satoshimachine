# Description: Pydantic data models dictate what is passed between frontend and backend.

from typing import Optional

from pydantic import BaseModel


class CreateSatoshiMachineData(BaseModel):
    id: Optional[str] = ""
    name: str
    lnurlpayamount: int
    lnurlwithdrawamount: int
    wallet: str
    total: int = 0


class SatoshiMachine(BaseModel):
    id: str
    name: str
    lnurlpayamount: int
    lnurlwithdrawamount: int
    wallet: str
    total: int
    lnurlpay: Optional[str] = ""
    lnurlwithdraw: Optional[str] = ""


class CreatePayment(BaseModel):
    satoshimachine_id: str
    amount: int
    memo: str
