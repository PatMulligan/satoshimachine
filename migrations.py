# the migration file is where you build your database tables
# If you create a new release for your extension ,
# remember the migration file is like a blockchain, never edit only add!

# DCA Admin Extension - Database Migrations

async def m001_initial_tables(db):
    """
    Creates the initial tables for the DCA admin extension.
    Migrates from SatoshiMachine template to DCA system.
    """
    
    # DCA Clients table
    await db.execute(
        """
        CREATE TABLE dca_admin.clients (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            wallet_id TEXT NOT NULL,
            initial_deposit DECIMAL(15,2) NOT NULL,
            current_balance DECIMAL(15,2) NOT NULL DEFAULT 0,
            total_distributed DECIMAL(15,2) NOT NULL DEFAULT 0,
            total_satoshis INTEGER NOT NULL DEFAULT 0,
            dca_mode TEXT NOT NULL DEFAULT 'flow',
            fixed_daily_limit DECIMAL(15,2),
            daily_distributed_today DECIMAL(15,2) NOT NULL DEFAULT 0,
            last_distribution TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    
    # Processed Transactions table (for duplicate prevention)
    await db.execute(
        """
        CREATE TABLE dca_admin.processed_transactions (
            id TEXT PRIMARY KEY,
            lamassu_transaction_id TEXT UNIQUE NOT NULL,
            processing_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            flow_distribution_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
            commission_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
            clients_affected INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'completed'
        );
        """
    )
    
    # DCA Distributions table
    await db.execute(
        """
        CREATE TABLE dca_admin.distributions (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            transaction_id TEXT,
            amount_fiat DECIMAL(15,2) NOT NULL,
            amount_satoshis INTEGER NOT NULL,
            exchange_rate DECIMAL(15,8) NOT NULL,
            distribution_type TEXT NOT NULL,
            payment_hash TEXT,
            payment_request TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES dca_admin.clients (id),
            FOREIGN KEY (transaction_id) REFERENCES dca_admin.processed_transactions (id)
        );
        """
    )
    
    # Commission Recipients table
    await db.execute(
        """
        CREATE TABLE dca_admin.commission_recipients (
            id TEXT PRIMARY KEY,
            wallet_id TEXT NOT NULL,
            wallet_name TEXT NOT NULL,
            allocation_percentage DECIMAL(5,2) NOT NULL,
            recipient_type TEXT NOT NULL DEFAULT 'external',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    
    # Commission Distributions table
    await db.execute(
        """
        CREATE TABLE dca_admin.commission_distributions (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            amount_fiat DECIMAL(15,2) NOT NULL,
            amount_satoshis INTEGER NOT NULL,
            exchange_rate DECIMAL(15,8) NOT NULL,
            payment_hash TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES dca_admin.processed_transactions (id),
            FOREIGN KEY (recipient_id) REFERENCES dca_admin.commission_recipients (id)
        );
        """
    )
    
    # System Configuration table
    await db.execute(
        """
        CREATE TABLE dca_admin.system_config (
            id TEXT PRIMARY KEY DEFAULT 'default',
            lamassu_server_ip TEXT,
            lamassu_ssh_user TEXT NOT NULL DEFAULT 'root',
            lamassu_log_dir TEXT NOT NULL DEFAULT './lamassu_logs',
            last_processed_timestamp TIMESTAMP,
            fixed_mode_schedule TEXT NOT NULL DEFAULT 'daily',
            fixed_mode_time TEXT NOT NULL DEFAULT '09:00',
            max_daily_fixed_amount DECIMAL(15,2) NOT NULL DEFAULT 2000,
            processing_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            nostr_relay TEXT,
            notification_wallet TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    
    # Create indexes for performance
    await db.execute("CREATE INDEX idx_clients_user_id ON dca_admin.clients (user_id);")
    await db.execute("CREATE INDEX idx_clients_wallet_id ON dca_admin.clients (wallet_id);")
    await db.execute("CREATE INDEX idx_clients_status ON dca_admin.clients (status);")
    await db.execute("CREATE INDEX idx_clients_dca_mode ON dca_admin.clients (dca_mode);")
    
    await db.execute("CREATE INDEX idx_processed_transactions_lamassu_id ON dca_admin.processed_transactions (lamassu_transaction_id);")
    await db.execute("CREATE INDEX idx_processed_transactions_timestamp ON dca_admin.processed_transactions (processing_timestamp);")
    
    await db.execute("CREATE INDEX idx_distributions_client_id ON dca_admin.distributions (client_id);")
    await db.execute("CREATE INDEX idx_distributions_transaction_id ON dca_admin.distributions (transaction_id);")
    await db.execute("CREATE INDEX idx_distributions_status ON dca_admin.distributions (status);")
    await db.execute("CREATE INDEX idx_distributions_created_at ON dca_admin.distributions (created_at);")
    
    await db.execute("CREATE INDEX idx_commission_recipients_status ON dca_admin.commission_recipients (status);")
    await db.execute("CREATE INDEX idx_commission_distributions_transaction_id ON dca_admin.commission_distributions (transaction_id);")
    await db.execute("CREATE INDEX idx_commission_distributions_recipient_id ON dca_admin.commission_distributions (recipient_id);")
    
    # Insert default system configuration
    await db.execute(
        """
        INSERT INTO dca_admin.system_config (
            id, created_at, updated_at
        ) VALUES (
            'default', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        );
        """
    )


async def m002_add_wallet_constraints(db):
    """
    Add unique constraints and additional indexes for wallet management.
    """
    # Ensure one DCA client per user (they can only have one active DCA)
    await db.execute("CREATE UNIQUE INDEX idx_clients_user_unique ON dca_admin.clients (user_id) WHERE status = 'active';")
    
    # Add index for daily distribution tracking
    await db.execute("CREATE INDEX idx_distributions_daily ON dca_admin.distributions (client_id, created_at);")
    

async def m003_add_transaction_metadata(db):
    """
    Add additional fields for enhanced transaction tracking.
    """
    # Add more detailed transaction tracking
    await db.execute("ALTER TABLE dca_admin.processed_transactions ADD COLUMN fiat_code TEXT DEFAULT 'GTQ';")
    await db.execute("ALTER TABLE dca_admin.processed_transactions ADD COLUMN crypto_code TEXT DEFAULT 'BTC';")
    await db.execute("ALTER TABLE dca_admin.processed_transactions ADD COLUMN machine_id TEXT;")
    await db.execute("ALTER TABLE dca_admin.processed_transactions ADD COLUMN exchange_rate DECIMAL(15,8);")
    
    # Add performance tracking to clients
    await db.execute("ALTER TABLE dca_admin.clients ADD COLUMN average_rate DECIMAL(15,8) DEFAULT 0;")
    await db.execute("ALTER TABLE dca_admin.clients ADD COLUMN distribution_count INTEGER DEFAULT 0;")


async def m004_cleanup_old_tables(db):
    """
    Clean up old SatoshiMachine tables since we're repurposing this extension.
    """
    # Remove old SatoshiMachine tables if they exist
    try:
        await db.execute("DROP TABLE IF EXISTS dca_admin.maintable;")
    except Exception:
        pass  # Table might not exist
