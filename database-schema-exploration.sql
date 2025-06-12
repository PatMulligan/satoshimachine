-- Database Schema Exploration for Lamassu ATM
-- Run these queries to understand the database structure

-- 1. List all tables in the database
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 2. Get detailed column information for all tables
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

-- 3. Look for transaction-related tables (common naming patterns)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (
    table_name ILIKE '%transaction%' OR
    table_name ILIKE '%tx%' OR
    table_name ILIKE '%payment%' OR
    table_name ILIKE '%cash%' OR
    table_name ILIKE '%trade%' OR
    table_name ILIKE '%order%'
)
ORDER BY table_name;

-- 4. Once you identify the main transaction table, explore its structure
-- Replace 'transactions' with the actual table name
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'transactions'  -- Replace with actual table name
ORDER BY ordinal_position;

-- 5. Get sample data from the transaction table (limit to 5 rows)
-- Replace 'transactions' with the actual table name
SELECT * FROM transactions LIMIT 5;

-- 6. Look for status/state columns that indicate success/failure
-- Replace 'transactions' with the actual table name
SELECT DISTINCT status FROM transactions;  -- or 'state', 'tx_status', etc.

-- 7. Check for indexes and constraints
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'transactions';  -- Replace with actual table name

-- 8. Look for foreign key relationships
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'; 