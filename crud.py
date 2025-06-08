# Description: This file contains the CRUD operations for talking to the database.

from typing import List, Optional, Union

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreateMyExtensionData, MyExtension

db = Database("ext_satoshimachine")


async def create_satoshimachine(data: CreateMyExtensionData) -> MyExtension:
    data.id = urlsafe_short_hash()
    await db.insert("satoshimachine.maintable", data)
    return MyExtension(**data.dict())


async def get_satoshimachine(satoshimachine_id: str) -> Optional[MyExtension]:
    return await db.fetchone(
        "SELECT * FROM satoshimachine.maintable WHERE id = :id",
        {"id": satoshimachine_id},
        MyExtension,
    )


async def get_satoshimachines(wallet_ids: Union[str, List[str]]) -> List[MyExtension]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]
    q = ",".join([f"'{w}'" for w in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM satoshimachine.maintable WHERE wallet IN ({q}) ORDER BY id",
        model=MyExtension,
    )


async def update_satoshimachine(data: CreateMyExtensionData) -> MyExtension:
    await db.update("satoshimachine.maintable", data)
    return MyExtension(**data.dict())


async def delete_satoshimachine(satoshimachine_id: str) -> None:
    await db.execute(
        "DELETE FROM satoshimachine.maintable WHERE id = :id", {"id": satoshimachine_id}
    )
