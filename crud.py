# Description: This file contains the CRUD operations for talking to the database.

from typing import List, Optional, Union

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreateSatoshiMachineData, SatoshiMachine

db = Database("ext_satoshimachine")


async def create_satoshimachine(data: CreateSatoshiMachineData) -> SatoshiMachine:
    data.id = urlsafe_short_hash()
    await db.insert("satoshimachine.maintable", data)
    return SatoshiMachine(**data.dict())


async def get_satoshimachine(satoshimachine_id: str) -> Optional[SatoshiMachine]:
    return await db.fetchone(
        "SELECT * FROM satoshimachine.maintable WHERE id = :id",
        {"id": satoshimachine_id},
        SatoshiMachine,
    )


async def get_satoshimachines(wallet_ids: Union[str, List[str]]) -> List[SatoshiMachine]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]
    q = ",".join([f"'{w}'" for w in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM satoshimachine.maintable WHERE wallet IN ({q}) ORDER BY id",
        model=SatoshiMachine,
    )


async def update_satoshimachine(data: CreateSatoshiMachineData) -> SatoshiMachine:
    await db.update("satoshimachine.maintable", data)
    return SatoshiMachine(**data.dict())


async def delete_satoshimachine(satoshimachine_id: str) -> None:
    await db.execute(
        "DELETE FROM satoshimachine.maintable WHERE id = :id", {"id": satoshimachine_id}
    )
