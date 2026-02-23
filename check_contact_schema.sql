-- Run this in Azure PostgreSQL Query Editor to check the actual column types
-- This will show us if there's a type mismatch

-- Check contacts_contact table structure
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'contacts_contact'
ORDER BY ordinal_position;

-- Check tenant_tenant table structure
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'tenant_tenant'
ORDER BY ordinal_position;

-- Check if there's a foreign key constraint between them
SELECT
    tc.constraint_name,
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
    AND tc.table_name = 'contacts_contact'
    AND kcu.column_name = 'tenant_id';

-- Sample contacts with their tenant_id values and types
SELECT
    id,
    phone,
    name,
    "createdOn",
    tenant_id,
    pg_typeof(tenant_id) as tenant_id_type
FROM contacts_contact
LIMIT 10;

-- Count contacts by tenant_id
SELECT
    tenant_id,
    COUNT(*) as contact_count
FROM contacts_contact
GROUP BY tenant_id
ORDER BY contact_count DESC;
