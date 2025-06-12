#!/usr/bin/env python3
"""
Transaction Data Fetcher for DCA Admin Extension
Integrates the bash script logic into Python for seamless LNBits integration
"""

import os
import subprocess
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import csv
from io import StringIO

logger = logging.getLogger(__name__)

class LamassuTransactionFetcher:
    """Handles fetching and processing transaction data from Lamassu ATM"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize with configuration
        
        Args:
            config: Dictionary containing:
                - server_ip: IP address of Lamassu server
                - server_log_dir: Directory to store current CSV files
                - old_server_log_dir: Directory to archive old CSV files
                - ssh_user: SSH username (default: root)
        """
        self.server_ip = config['server_ip']
        self.server_log_dir = Path(config['server_log_dir'])
        self.old_server_log_dir = Path(config['old_server_log_dir'])
        self.ssh_user = config.get('ssh_user', 'root')
        
        # Ensure directories exist
        self.server_log_dir.mkdir(parents=True, exist_ok=True)
        self.old_server_log_dir.mkdir(parents=True, exist_ok=True)
        
        # File names
        self.files = {
            'cash_out': 'cash_out_txs.csv',
            'cash_in': 'cash_in_txs.csv', 
            'out_actions': 'cash_out_actions.csv'
        }
    
    def archive_existing_files(self) -> None:
        """Archive existing CSV files with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        for file_type, filename in self.files.items():
            file_path = self.server_log_dir / filename
            
            if file_path.exists():
                # Create archived filename
                base_name = file_path.stem
                archived_name = f"{base_name}_{timestamp}.csv"
                archived_path = self.old_server_log_dir / archived_name
                
                # Move file to archive
                file_path.rename(archived_path)
                logger.info(f"Archived {filename} to {archived_name}")
            else:
                logger.info(f"No previous {filename} exists")
    
    def fetch_remote_data(self) -> bool:
        """
        Execute remote commands to export data and download CSV files
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Execute export commands on remote server
            export_commands = [
                'export-cash-out',
                'export-cash-in', 
                'export-out-actions'
            ]
            
            for command in export_commands:
                ssh_cmd = ['ssh', f'{self.ssh_user}@{self.server_ip}', command]
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    logger.error(f"Failed to execute {command}: {result.stderr}")
                    return False
                    
                logger.info(f"Successfully executed {command}")
            
            # Download exported files
            remote_files = {
                'cash_out': '/tmp/cash_out_txs.csv',
                'cash_in': '/tmp/cash_in_txs.csv',
                'out_actions': '/tmp/cash_out_actions.csv'
            }
            
            for file_type, remote_path in remote_files.items():
                local_path = self.server_log_dir / self.files[file_type]
                scp_cmd = [
                    'scp', 
                    f'{self.ssh_user}@{self.server_ip}:{remote_path}',
                    str(local_path)
                ]
                
                result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    logger.error(f"Failed to download {remote_path}: {result.stderr}")
                    return False
                    
                logger.info(f"Downloaded {remote_path} to {local_path}")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("SSH/SCP command timed out")
            return False
        except Exception as e:
            logger.error(f"Error fetching remote data: {e}")
            return False
    
    def parse_cash_out_transactions(self) -> List[Dict]:
        """
        Parse cash-out transactions CSV for DCA processing
        
        Returns:
            List of transaction dictionaries with relevant fields
        """
        csv_path = self.server_log_dir / self.files['cash_out']
        
        if not csv_path.exists():
            logger.warning(f"Cash-out CSV file not found: {csv_path}")
            return []
        
        transactions = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Read CSV without headers (based on sample data format)
                csv_reader = csv.reader(file)
                
                for row in csv_reader:
                    if len(row) >= 32:  # Ensure minimum required columns
                        try:
                            transaction = {
                                'id': row[0],
                                'device_id': row[1], 
                                'crypto_address': row[2],
                                'crypto_atoms': int(row[3]) if row[3] else 0,
                                'crypto_code': row[4],
                                'fiat_amount': float(row[5]) if row[5] else 0.0,
                                'fiat_code': row[6],
                                'status': row[7],
                                'send': row[8] == 't',
                                'receive': row[9] == 't',
                                'error_code': row[11] if row[11] else None,
                                'created': row[12],
                                'send_confirmed': row[13] if row[13] else None,
                                'confirmations': int(row[18]) if row[18] else 0,
                                'discount_percentage': float(row[20]) if row[20] else 0.0,
                                'cancel_reason': row[22] if row[22] else None,
                                'machine_id': row[23],
                                'batch_id': row[24],
                                'commission_percentage': float(row[29]) if row[29] else 0.0,
                                'exchange_rate': float(row[30]) if row[30] else 0.0,
                                'dispensed': int(row[31]) if row[31] else 0,
                            }
                            
                            transactions.append(transaction)
                            
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Error parsing transaction row: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error reading cash-out CSV: {e}")
            return []
        
        logger.info(f"Parsed {len(transactions)} cash-out transactions")
        return transactions
    
    def filter_dca_transactions(self, transactions: List[Dict], 
                               last_processed_time: Optional[datetime] = None) -> List[Dict]:
        """
        Filter transactions for DCA processing
        
        Args:
            transactions: List of parsed transactions
            last_processed_time: Only return transactions after this time
            
        Returns:
            List of transactions suitable for DCA distribution
        """
        filtered = []
        
        for tx in transactions:
            # Must be successful cash-out transaction
            if (tx['status'] == 'confirmed' and 
                tx['send'] == True and 
                tx['error_code'] is None and 
                tx['cancel_reason'] is None):
                
                # Check if after last processed time
                if last_processed_time:
                    try:
                        tx_time = datetime.fromisoformat(tx['created'].replace('+00', '+00:00'))
                        if tx_time <= last_processed_time:
                            continue
                    except ValueError:
                        logger.warning(f"Invalid date format in transaction {tx['id']}")
                        continue
                
                # Calculate actual commission and distribution amount
                base_commission = tx['fiat_amount'] * tx['commission_percentage']
                actual_commission = base_commission * (1 - tx['discount_percentage']/100)
                distribution_amount = tx['fiat_amount'] - actual_commission
                
                tx['actual_commission'] = actual_commission
                tx['distribution_amount'] = distribution_amount
                
                filtered.append(tx)
        
        logger.info(f"Filtered {len(filtered)} transactions for DCA processing")
        return filtered
    
    def fetch_and_process(self, last_processed_time: Optional[datetime] = None) -> Tuple[bool, List[Dict]]:
        """
        Complete fetch and process cycle
        
        Args:
            last_processed_time: Only return transactions after this time
            
        Returns:
            Tuple of (success: bool, transactions: List[Dict])
        """
        # Archive existing files
        self.archive_existing_files()
        
        # Fetch new data
        if not self.fetch_remote_data():
            return False, []
        
        # Parse transactions
        transactions = self.parse_cash_out_transactions()
        
        # Filter for DCA processing
        dca_transactions = self.filter_dca_transactions(transactions, last_processed_time)
        
        return True, dca_transactions

# Example usage for LNBits integration
def create_fetcher_from_env() -> LamassuTransactionFetcher:
    """Create fetcher instance from environment variables"""
    config = {
        'server_ip': os.getenv('LAMASSU_SERVER_IP'),
        'server_log_dir': os.getenv('LAMASSU_LOG_DIR', './lamassu_logs'),
        'old_server_log_dir': os.getenv('LAMASSU_OLD_LOG_DIR', './lamassu_logs/archive'),
        'ssh_user': os.getenv('LAMASSU_SSH_USER', 'root')
    }
    
    # Validate required config
    if not config['server_ip']:
        raise ValueError("LAMASSU_SERVER_IP environment variable required")
    
    return LamassuTransactionFetcher(config)

if __name__ == "__main__":
    # Test the fetcher
    fetcher = create_fetcher_from_env()
    success, transactions = fetcher.fetch_and_process()
    
    if success:
        print(f"Successfully fetched {len(transactions)} new DCA transactions")
        for tx in transactions[:3]:  # Show first 3
            print(f"TX {tx['id']}: {tx['fiat_amount']} {tx['fiat_code']} -> {tx['distribution_amount']} for DCA")
    else:
        print("Failed to fetch transaction data") 