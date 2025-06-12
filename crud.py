# Description: DCA Admin Extension - Database Operations

from datetime import datetime
from typing import List, Optional, Union
from decimal import Decimal

from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import (
    CreateDCAClientData,
    DCAClient,
    CreateCommissionRecipientData,
    CommissionRecipient,
    UpdateSystemConfigData,
    SystemConfig,
    DCAMetrics,
    ClientMetrics,
    ProcessedTransaction,
    DCADistribution,
    CommissionDistribution,
)

db = Database("ext_dca_admin")

#######################################
##### DCA CLIENT OPERATIONS ##########
#######################################

async def create_dca_client(data: CreateDCAClientData, wallet_id: str) -> DCAClient:
    """Create a new DCA client."""
    client_id = urlsafe_short_hash()
    now = datetime.utcnow()
    
    client_data = {
        "id": client_id,
        "user_id": data.user_id,
        "wallet_id": data.wallet_id,
        "initial_deposit": data.initial_deposit,
        "current_balance": data.initial_deposit,
        "total_distributed": Decimal("0"),
        "total_satoshis": 0,
        "dca_mode": data.dca_mode,
        "fixed_daily_limit": data.fixed_daily_limit,
        "daily_distributed_today": Decimal("0"),
        "last_distribution": None,
        "status": "active",
        "notes": data.notes,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.execute(
        """
        INSERT INTO dca_admin.clients (
            id, user_id, wallet_id, initial_deposit, current_balance,
            total_distributed, total_satoshis, dca_mode, fixed_daily_limit,
            daily_distributed_today, last_distribution, status, notes,
            created_at, updated_at
        ) VALUES (
            :id, :user_id, :wallet_id, :initial_deposit, :current_balance,
            :total_distributed, :total_satoshis, :dca_mode, :fixed_daily_limit,
            :daily_distributed_today, :last_distribution, :status, :notes,
            :created_at, :updated_at
        )
        """,
        client_data,
    )
    
    return DCAClient(**client_data)

async def get_dca_client(client_id: str) -> Optional[DCAClient]:
    """Get a specific DCA client."""
    return await db.fetchone(
        "SELECT * FROM dca_admin.clients WHERE id = :id",
        {"id": client_id},
        DCAClient,
    )

async def get_dca_clients(wallet_id: str) -> List[DCAClient]:
    """Get all DCA clients for a wallet."""
    return await db.fetchall(
        "SELECT * FROM dca_admin.clients WHERE wallet_id = :wallet_id ORDER BY created_at DESC",
        {"wallet_id": wallet_id},
        DCAClient,
    )

async def update_dca_client(client_id: str, data: CreateDCAClientData) -> DCAClient:
    """Update a DCA client."""
    now = datetime.utcnow()
    
    await db.execute(
        """
        UPDATE dca_admin.clients SET
            dca_mode = :dca_mode,
            fixed_daily_limit = :fixed_daily_limit,
            notes = :notes,
            updated_at = :updated_at
        WHERE id = :id
        """,
        {
            "id": client_id,
            "dca_mode": data.dca_mode,
            "fixed_daily_limit": data.fixed_daily_limit,
            "notes": data.notes,
            "updated_at": now,
        },
    )
    
    return await get_dca_client(client_id)

async def delete_dca_client(client_id: str) -> None:
    """Delete a DCA client."""
    await db.execute(
        "DELETE FROM dca_admin.clients WHERE id = :id",
        {"id": client_id},
    )

#######################################
##### COMMISSION RECIPIENT OPERATIONS #
#######################################

async def create_commission_recipient(data: CreateCommissionRecipientData, wallet_id: str) -> CommissionRecipient:
    """Create a new commission recipient."""
    recipient_id = urlsafe_short_hash()
    now = datetime.utcnow()
    
    recipient_data = {
        "id": recipient_id,
        "wallet_id": data.wallet_id,
        "wallet_name": data.wallet_name,
        "allocation_percentage": data.allocation_percentage,
        "recipient_type": data.recipient_type,
        "status": "active",
        "created_at": now,
    }
    
    await db.execute(
        """
        INSERT INTO dca_admin.commission_recipients (
            id, wallet_id, wallet_name, allocation_percentage,
            recipient_type, status, created_at
        ) VALUES (
            :id, :wallet_id, :wallet_name, :allocation_percentage,
            :recipient_type, :status, :created_at
        )
        """,
        recipient_data,
    )
    
    return CommissionRecipient(**recipient_data)

async def get_commission_recipients(wallet_id: str) -> List[CommissionRecipient]:
    """Get all commission recipients."""
    return await db.fetchall(
        "SELECT * FROM dca_admin.commission_recipients ORDER BY created_at DESC",
        model=CommissionRecipient,
    )

async def update_commission_recipient(recipient_id: str, data: CreateCommissionRecipientData) -> CommissionRecipient:
    """Update a commission recipient."""
    await db.execute(
        """
        UPDATE dca_admin.commission_recipients SET
            wallet_id = :wallet_id,
            wallet_name = :wallet_name,
            allocation_percentage = :allocation_percentage,
            recipient_type = :recipient_type
        WHERE id = :id
        """,
        {
            "id": recipient_id,
            "wallet_id": data.wallet_id,
            "wallet_name": data.wallet_name,
            "allocation_percentage": data.allocation_percentage,
            "recipient_type": data.recipient_type,
        },
    )
    
    return await db.fetchone(
        "SELECT * FROM dca_admin.commission_recipients WHERE id = :id",
        {"id": recipient_id},
        CommissionRecipient,
    )

async def delete_commission_recipient(recipient_id: str) -> None:
    """Delete a commission recipient."""
    await db.execute(
        "DELETE FROM dca_admin.commission_recipients WHERE id = :id",
        {"id": recipient_id},
    )

#######################################
##### SYSTEM CONFIG OPERATIONS #######
#######################################

async def get_system_config() -> Optional[SystemConfig]:
    """Get system configuration."""
    return await db.fetchone(
        "SELECT * FROM dca_admin.system_config WHERE id = 'default'",
        model=SystemConfig,
    )

async def update_system_config(data: UpdateSystemConfigData) -> SystemConfig:
    """Update system configuration."""
    now = datetime.utcnow()
    
    # Get current config
    current = await get_system_config()
    if not current:
        # Create default config if it doesn't exist
        config_id = "default"
        await db.execute(
            """
            INSERT INTO dca_admin.system_config (
                id, created_at, updated_at
            ) VALUES (
                :id, :created_at, :updated_at
            )
            """,
            {
                "id": config_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        current = await get_system_config()
    
    # Update with new values
    update_data = data.dict(exclude_unset=True)
    update_data["updated_at"] = now
    
    await db.execute(
        """
        UPDATE dca_admin.system_config SET
            lamassu_server_ip = COALESCE(:lamassu_server_ip, lamassu_server_ip),
            lamassu_ssh_user = COALESCE(:lamassu_ssh_user, lamassu_ssh_user),
            lamassu_log_dir = COALESCE(:lamassu_log_dir, lamassu_log_dir),
            fixed_mode_schedule = COALESCE(:fixed_mode_schedule, fixed_mode_schedule),
            fixed_mode_time = COALESCE(:fixed_mode_time, fixed_mode_time),
            max_daily_fixed_amount = COALESCE(:max_daily_fixed_amount, max_daily_fixed_amount),
            processing_enabled = COALESCE(:processing_enabled, processing_enabled),
            nostr_relay = COALESCE(:nostr_relay, nostr_relay),
            notification_wallet = COALESCE(:notification_wallet, notification_wallet),
            updated_at = :updated_at
        WHERE id = 'default'
        """,
        update_data,
    )
    
    return await get_system_config()

#######################################
##### TRANSACTION OPERATIONS #########
#######################################

async def get_processed_transactions(wallet_id: str, limit: int = 100, offset: int = 0) -> List[ProcessedTransaction]:
    """Get processed transactions."""
    return await db.fetchall(
        """
        SELECT * FROM dca_admin.processed_transactions
        ORDER BY processing_timestamp DESC
        LIMIT :limit OFFSET :offset
        """,
        {"limit": limit, "offset": offset},
        ProcessedTransaction,
    )

async def get_dca_distributions(wallet_id: str, limit: int = 100, offset: int = 0) -> List[DCADistribution]:
    """Get DCA distributions."""
    return await db.fetchall(
        """
        SELECT d.* FROM dca_admin.distributions d
        JOIN dca_admin.clients c ON d.client_id = c.id
        WHERE c.wallet_id = :wallet_id
        ORDER BY d.created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        {"wallet_id": wallet_id, "limit": limit, "offset": offset},
        DCADistribution,
    )

async def get_commission_distributions(wallet_id: str, limit: int = 100, offset: int = 0) -> List[CommissionDistribution]:
    """Get commission distributions."""
    return await db.fetchall(
        """
        SELECT cd.* FROM dca_admin.commission_distributions cd
        JOIN dca_admin.commission_recipients cr ON cd.recipient_id = cr.id
        WHERE cr.wallet_id = :wallet_id
        ORDER BY cd.created_at DESC
        LIMIT :limit OFFSET :offset
        """,
        {"wallet_id": wallet_id, "limit": limit, "offset": offset},
        CommissionDistribution,
    )

#######################################
##### ANALYTICS OPERATIONS ###########
#######################################

async def get_dca_metrics(wallet_id: str) -> DCAMetrics:
    """Get system-wide DCA metrics."""
    # Get total clients
    total_clients = await db.fetchone(
        "SELECT COUNT(*) as count FROM dca_admin.clients",
        {"wallet_id": wallet_id},
    )
    
    # Get active clients
    active_clients = await db.fetchone(
        "SELECT COUNT(*) as count FROM dca_admin.clients WHERE status = 'active'",
        {"wallet_id": wallet_id},
    )
    
    # Get flow mode clients
    flow_clients = await db.fetchone(
        "SELECT COUNT(*) as count FROM dca_admin.clients WHERE dca_mode = 'flow'",
        {"wallet_id": wallet_id},
    )
    
    # Get fixed mode clients
    fixed_clients = await db.fetchone(
        "SELECT COUNT(*) as count FROM dca_admin.clients WHERE dca_mode = 'fixed'",
        {"wallet_id": wallet_id},
    )
    
    # Get total deposits and distributions
    totals = await db.fetchone(
        """
        SELECT 
            SUM(initial_deposit) as total_deposits,
            SUM(total_distributed) as total_distributed,
            SUM(total_satoshis) as total_satoshis
        FROM dca_admin.clients
        """,
        {"wallet_id": wallet_id},
    )
    
    # Get today's transactions
    today_transactions = await db.fetchone(
        """
        SELECT COUNT(*) as count
        FROM dca_admin.processed_transactions
        WHERE DATE(processing_timestamp) = CURRENT_DATE
        """,
        {"wallet_id": wallet_id},
    )
    
    # Get last transaction time
    last_transaction = await db.fetchone(
        """
        SELECT processing_timestamp
        FROM dca_admin.processed_transactions
        ORDER BY processing_timestamp DESC
        LIMIT 1
        """,
        {"wallet_id": wallet_id},
    )
    
    return DCAMetrics(
        total_clients=total_clients["count"] if total_clients else 0,
        active_clients=active_clients["count"] if active_clients else 0,
        flow_mode_clients=flow_clients["count"] if flow_clients else 0,
        fixed_mode_clients=fixed_clients["count"] if fixed_clients else 0,
        total_deposits=totals["total_deposits"] if totals else Decimal("0"),
        total_distributed=totals["total_distributed"] if totals else Decimal("0"),
        total_satoshis_distributed=totals["total_satoshis"] if totals else 0,
        average_dca_rate=Decimal("0"),  # TODO: Calculate from historical data
        transactions_processed_today=today_transactions["count"] if today_transactions else 0,
        last_transaction_time=last_transaction["processing_timestamp"] if last_transaction else None,
    )

async def get_client_metrics(client_id: str) -> ClientMetrics:
    """Get metrics for a specific client."""
    # Get client data
    client = await get_dca_client(client_id)
    if not client:
        raise ValueError("Client not found")
    
    # Get distribution count
    distribution_count = await db.fetchone(
        """
        SELECT COUNT(*) as count
        FROM dca_admin.distributions
        WHERE client_id = :client_id
        """,
        {"client_id": client_id},
    )
    
    # Get last distribution
    last_distribution = await db.fetchone(
        """
        SELECT created_at
        FROM dca_admin.distributions
        WHERE client_id = :client_id
        ORDER BY created_at DESC
        LIMIT 1
        """,
        {"client_id": client_id},
    )
    
    return ClientMetrics(
        client_id=client_id,
        total_invested=client.initial_deposit,
        total_satoshis=client.total_satoshis,
        average_rate=client.average_rate if hasattr(client, "average_rate") else Decimal("0"),
        distribution_count=distribution_count["count"] if distribution_count else 0,
        last_distribution=last_distribution["created_at"] if last_distribution else None,
        performance_vs_spot=Decimal("0"),  # TODO: Calculate from historical data
    )
