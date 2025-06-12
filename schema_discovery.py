#!/usr/bin/env python3
"""
Database Schema Discovery Script for Lamassu ATM
This script connects to the Postgres database and exports the schema information
"""

import psycopg2
import json
import csv
from datetime import datetime

def connect_to_database(host, port, database, username, password):
    """Connect to the Postgres database"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_all_tables(cursor):
    """Get list of all tables in the public schema"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_structure(cursor, table_name):
    """Get detailed structure of a specific table"""
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'column_name': row[0],
            'data_type': row[1],
            'is_nullable': row[2],
            'column_default': row[3],
            'max_length': row[4]
        })
    
    return columns

def get_sample_data(cursor, table_name, limit=3):
    """Get sample data from a table"""
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting sample data from {table_name}: {e}")
        return []

def discover_schema(host, port, database, username, password):
    """Main function to discover and document database schema"""
    
    # Connect to database
    conn = connect_to_database(host, port, database, username, password)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Get all tables
    print("Discovering database schema...")
    tables = get_all_tables(cursor)
    print(f"Found {len(tables)} tables")
    
    schema_info = {
        'discovery_date': datetime.now().isoformat(),
        'database': database,
        'tables': {}
    }
    
    # Analyze each table
    for table_name in tables:
        print(f"Analyzing table: {table_name}")
        
        # Get table structure
        columns = get_table_structure(cursor, table_name)
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get sample data
        sample_data = get_sample_data(cursor, table_name)
        
        schema_info['tables'][table_name] = {
            'row_count': row_count,
            'columns': columns,
            'sample_data': sample_data[:3]  # Limit to first 3 rows
        }
        
        # Check if this looks like a transaction table
        transaction_indicators = ['transaction', 'tx', 'payment', 'cash', 'trade', 'order']
        if any(indicator in table_name.lower() for indicator in transaction_indicators):
            print(f"  -> Potential transaction table: {table_name}")
    
    # Save schema to JSON file
    with open(f'lamassu_schema_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(schema_info, f, indent=2, default=str)
    
    # Create a summary CSV
    with open(f'lamassu_tables_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Table Name', 'Row Count', 'Column Count', 'Potential Transaction Table'])
        
        for table_name, info in schema_info['tables'].items():
            transaction_indicators = ['transaction', 'tx', 'payment', 'cash', 'trade', 'order']
            is_transaction = any(indicator in table_name.lower() for indicator in transaction_indicators)
            writer.writerow([
                table_name, 
                info['row_count'], 
                len(info['columns']),
                'Yes' if is_transaction else 'No'
            ])
    
    cursor.close()
    conn.close()
    
    print("\nSchema discovery complete!")
    print("Files created:")
    print(f"- lamassu_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    print(f"- lamassu_tables_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

if __name__ == "__main__":
    # Configuration - update these values
    DB_CONFIG = {
        'host': 'your_lamassu_host',
        'port': 5432,
        'database': 'your_database_name',
        'username': 'your_username',
        'password': 'your_password'
    }
    
    print("Lamassu Database Schema Discovery")
    print("=" * 40)
    
    # Update the configuration above with your actual database credentials
    discover_schema(**DB_CONFIG) 