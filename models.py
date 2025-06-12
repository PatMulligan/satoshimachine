# Description: Pydantic data models dictate what is passed between frontend and backend.

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


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
    dca_admin_id: str
    amount: int
    memo: str


# DCA Admin Extension - Data Models
# Defines the data structures for Dollar Cost Averaging system

class DCAMode(str, Enum):
    """DCA operation modes"""
    FLOW = "flow"      # Triggered by layperson transactions
    FIXED = "fixed"    # Scheduled distributions


class TransactionStatus(str, Enum):
    """Lamassu transaction statuses"""
    CONFIRMED = "confirmed"
    NOT_SEEN = "notSeen"
    PENDING = "pending"
    FAILED = "failed"


class DistributionType(str, Enum):
    """Types of DCA distributions"""
    FLOW = "flow"           # Flow mode distribution
    FIXED = "fixed"         # Fixed mode distribution
    MANUAL = "manual"       # Manual distribution
    COMMISSION = "commission"  # Commission distribution


# ============ DCA CLIENT MODELS ============

class CreateDCAClientData(BaseModel):
    """Data for creating a new DCA client"""
    user_id: str = Field(..., description="LNBits user ID")
    wallet_id: str = Field(..., description="Selected LNBits wallet ID for DCA")
    initial_deposit: Decimal = Field(..., description="Initial deposit amount in GTQ")
    dca_mode: DCAMode = Field(default=DCAMode.FLOW, description="DCA operation mode")
    fixed_daily_limit: Optional[Decimal] = Field(None, description="Daily limit for fixed mode (max 2000 GTQ)")
    notes: Optional[str] = Field(None, description="Admin notes about the client")


class DCAClient(BaseModel):
    """DCA client information"""
    id: str
    user_id: str
    wallet_id: str
    initial_deposit: Decimal
    current_balance: Decimal  # Remaining deposit balance
    total_distributed: Decimal  # Total amount distributed to client
    total_satoshis: int  # Total satoshis received
    dca_mode: DCAMode
    fixed_daily_limit: Optional[Decimal]
    daily_distributed_today: Decimal  # Amount distributed today (for fixed mode)
    last_distribution: Optional[datetime]
    status: str = "active"  # active, inactive, suspended
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class UpdateDCAClientData(BaseModel):
    """Data for updating DCA client settings"""
    dca_mode: Optional[DCAMode] = None
    fixed_daily_limit: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ============ TRANSACTION MODELS ============

class LamassuTransaction(BaseModel):
    """Parsed Lamassu transaction data"""
    id: str  # Transaction UUID from Lamassu
    device_id: str
    crypto_address: str
    crypto_atoms: int  # Amount in satoshis
    crypto_code: str  # BTC or LN
    fiat_amount: Decimal  # Requested fiat amount
    fiat_code: str  # GTQ
    status: TransactionStatus
    send: bool  # Send transaction flag
    receive: bool  # Receive transaction flag
    error_code: Optional[str]
    created: datetime
    send_confirmed: Optional[datetime]
    confirmations: int
    discount_percentage: Decimal  # Discount on commission
    cancel_reason: Optional[str]
    machine_id: str
    batch_id: Optional[str]
    commission_percentage: Decimal  # Base commission rate
    exchange_rate: Decimal  # Exchange rate at transaction time
    dispensed: int  # Actually dispensed amount
    
    # Calculated fields
    actual_commission: Optional[Decimal] = None  # Commission after discount
    distribution_amount: Optional[Decimal] = None  # Amount for DCA distribution


class ProcessedTransaction(BaseModel):
    """Record of processed transactions for duplicate prevention"""
    id: str
    lamassu_transaction_id: str  # Reference to Lamassu transaction
    processing_timestamp: datetime
    flow_distribution_amount: Decimal  # Amount distributed to flow mode clients
    commission_amount: Decimal  # Commission amount distributed separately
    clients_affected: int  # Number of flow mode clients affected
    status: str = "completed"  # completed, failed, partial


# ============ DISTRIBUTION MODELS ============

class DCADistribution(BaseModel):
    """Individual DCA distribution record"""
    id: str
    client_id: str
    transaction_id: Optional[str]  # Reference to processed transaction (if applicable)
    amount_fiat: Decimal  # Fiat amount of this distribution
    amount_satoshis: int  # Satoshis distributed
    exchange_rate: Decimal  # Exchange rate used
    distribution_type: DistributionType
    payment_hash: Optional[str]  # LNBits payment hash
    payment_request: Optional[str]  # Lightning invoice
    status: str = "pending"  # pending, completed, failed
    created_at: datetime
    completed_at: Optional[datetime]
    notes: Optional[str]


class CreateDistributionData(BaseModel):
    """Data for creating manual distributions"""
    client_id: str
    amount_fiat: Decimal
    distribution_type: DistributionType = DistributionType.MANUAL
    notes: Optional[str] = None


# ============ COMMISSION MODELS ============

class CommissionRecipient(BaseModel):
    """Configuration for commission distribution recipients"""
    id: str
    wallet_id: str  # LNBits wallet ID
    wallet_name: str  # Display name
    allocation_percentage: Decimal  # Percentage of commission (0-100)
    recipient_type: str = "external"  # external, dca_client
    status: str = "active"  # active, inactive
    created_at: datetime


class CreateCommissionRecipientData(BaseModel):
    """Data for creating commission recipients"""
    wallet_id: str
    wallet_name: str
    allocation_percentage: Decimal = Field(..., ge=0, le=100)
    recipient_type: str = "external"


class CommissionDistribution(BaseModel):
    """Record of commission distributions"""
    id: str
    transaction_id: str  # Reference to processed transaction
    recipient_id: str  # Reference to commission recipient
    amount_fiat: Decimal
    amount_satoshis: int
    exchange_rate: Decimal
    payment_hash: Optional[str]
    status: str = "pending"
    created_at: datetime
    completed_at: Optional[datetime]


# ============ SYSTEM CONFIGURATION MODELS ============

class SystemConfig(BaseModel):
    """System-wide DCA configuration"""
    id: str = "default"
    lamassu_server_ip: Optional[str] = None
    lamassu_ssh_user: str = "root"
    lamassu_log_dir: str = "./lamassu_logs"
    last_processed_timestamp: Optional[datetime] = None
    fixed_mode_schedule: str = "daily"  # daily, twice_daily, custom
    fixed_mode_time: str = "09:00"  # UTC time for fixed distributions
    max_daily_fixed_amount: Decimal = Field(default=2000, description="Maximum daily fixed amount per client")
    processing_enabled: bool = True
    nostr_relay: Optional[str] = None  # For error notifications
    notification_wallet: Optional[str] = None  # Wallet for system notifications
    created_at: datetime
    updated_at: datetime


class UpdateSystemConfigData(BaseModel):
    """Data for updating system configuration"""
    lamassu_server_ip: Optional[str] = None
    lamassu_ssh_user: Optional[str] = None
    lamassu_log_dir: Optional[str] = None
    fixed_mode_schedule: Optional[str] = None
    fixed_mode_time: Optional[str] = None
    max_daily_fixed_amount: Optional[Decimal] = None
    processing_enabled: Optional[bool] = None
    nostr_relay: Optional[str] = None
    notification_wallet: Optional[str] = None


# ============ ANALYTICS MODELS ============

class DCAMetrics(BaseModel):
    """DCA system metrics and analytics"""
    total_clients: int
    active_clients: int
    flow_mode_clients: int
    fixed_mode_clients: int
    total_deposits: Decimal
    total_distributed: Decimal
    total_satoshis_distributed: int
    average_dca_rate: Decimal
    transactions_processed_today: int
    last_transaction_time: Optional[datetime]
    system_health: str  # healthy, warning, error


class ClientMetrics(BaseModel):
    """Individual client metrics"""
    client_id: str
    total_invested: Decimal
    total_satoshis: int
    average_rate: Decimal
    distribution_count: int
    last_distribution: Optional[datetime]
    performance_vs_spot: Decimal  # Performance compared to spot price
