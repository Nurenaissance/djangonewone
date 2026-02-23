-- ============================================================
-- SMART GROUPS DIAGNOSTIC QUERIES
-- Run these in Azure PostgreSQL Query Editor
-- ============================================================

-- QUERY 1: Check if contacts exist at all
-- ============================================================
SELECT COUNT(*) as total_contacts FROM contacts_contact;


-- QUERY 2: Check contacts by tenant
-- ============================================================
SELECT
    tenant_id,
    COUNT(*) as contact_count,
    MIN("createdOn") as earliest_contact,
    MAX("createdOn") as latest_contact
FROM contacts_contact
GROUP BY tenant_id
ORDER BY contact_count DESC;


-- QUERY 3: Check data types (CRITICAL!)
-- ============================================================
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'contacts_contact'
    AND column_name IN ('id', 'tenant_id', 'createdOn', 'phone')
ORDER BY ordinal_position;

-- ⚠️ IMPORTANT: tenant_id should be 'character varying', NOT 'integer'!


-- QUERY 4: Sample contacts for your tenant
-- ============================================================
-- Replace 'ai' with your actual tenant_id
SELECT
    id,
    phone,
    name,
    "createdOn",
    tenant_id,
    pg_typeof(tenant_id) as tenant_id_type,
    pg_typeof("createdOn") as created_on_type
FROM contacts_contact
WHERE tenant_id = 'ai'  -- ⚠️ CHANGE THIS TO YOUR TENANT ID
ORDER BY "createdOn" DESC
LIMIT 10;


-- QUERY 5: Contacts in your date range
-- ============================================================
-- This mimics what the smart groups filter should find
SELECT
    id,
    phone,
    name,
    "createdOn"
FROM contacts_contact
WHERE tenant_id = 'ai'  -- ⚠️ CHANGE THIS TO YOUR TENANT ID
    AND "createdOn" > '2024-11-30 22:45:00'
    AND "createdOn" < '2026-01-09 23:46:00'
ORDER BY "createdOn" DESC;


-- QUERY 6: Check for NULL createdOn values
-- ============================================================
SELECT
    tenant_id,
    COUNT(*) as null_created_count
FROM contacts_contact
WHERE "createdOn" IS NULL
GROUP BY tenant_id;


-- QUERY 7: Verify tenant exists in tenant_tenant table
-- ============================================================
SELECT
    id,
    organization,
    tier,
    pg_typeof(id) as id_type
FROM tenant_tenant
WHERE id = 'ai';  -- ⚠️ CHANGE THIS TO YOUR TENANT ID


-- QUERY 8: Check foreign key constraint
-- ============================================================
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'contacts_contact'
    AND kcu.column_name = 'tenant_id';


-- ============================================================
-- INTERPRETATION GUIDE
-- ============================================================

-- QUERY 1: Should show > 0 contacts
--   If 0: No contacts in database at all

-- QUERY 2: Your tenant_id should appear in results
--   If missing: Contacts have a different tenant_id value
--   Check tenant_id column for what values actually exist

-- QUERY 3: tenant_id should be 'character varying'
--   ⚠️ If 'integer': THIS IS THE PROBLEM!
--   Fix: Either change model or alter database column type

-- QUERY 4: Should show sample contacts with your tenant_id
--   If empty: tenant_id doesn't match (use value from QUERY 2)
--   Check createdOn values - should be timestamps

-- QUERY 5: Should show contacts in your date range
--   If empty: No contacts in that date range
--   If has results: Smart groups should work after fixes

-- QUERY 6: Should show 0 null values
--   If > 0: NULL createdOn values won't match date filters
--   Fix: UPDATE contacts SET createdOn = NOW() WHERE createdOn IS NULL

-- QUERY 7: Tenant should exist
--   If empty: Tenant doesn't exist in tenant_tenant table

-- QUERY 8: Should show foreign key constraint
--   Verify foreign_column_name type matches tenant_id type
