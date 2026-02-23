-- Quick Migration: Create Missing Analytics Tables
-- Run this on Azure PostgreSQL Query Editor

-- ==================== MESSAGE EVENTS TABLE ====================
CREATE TABLE IF NOT EXISTS message_events (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255) NOT NULL UNIQUE,

    -- Message Details
    template_id VARCHAR(255),
    template_name VARCHAR(255),
    conversation_id VARCHAR(255),

    -- Recipient Details
    recipient_phone VARCHAR(50) NOT NULL,
    recipient_name VARCHAR(255),
    contact_id INTEGER,

    -- Event Tracking
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,

    -- Status
    current_status VARCHAR(50) DEFAULT 'pending',
    failure_reason TEXT,

    -- Metadata
    message_type VARCHAR(50),
    campaign_id VARCHAR(255),
    broadcast_group_id INTEGER,

    -- Costs
    cost DECIMAL(10, 4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    conversation_category VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_message_events_tenant_id ON message_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_message_events_template_id ON message_events(template_id);
CREATE INDEX IF NOT EXISTS idx_message_events_sent_at ON message_events(sent_at);
CREATE INDEX IF NOT EXISTS idx_message_events_recipient_phone ON message_events(recipient_phone);
CREATE INDEX IF NOT EXISTS idx_message_events_tenant_sent_at ON message_events(tenant_id, sent_at);

-- ==================== BUTTON CLICKS TABLE ====================
CREATE TABLE IF NOT EXISTS button_clicks (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255) NOT NULL,
    button_id VARCHAR(255),
    button_text TEXT,
    button_type VARCHAR(50),
    button_index INTEGER,
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recipient_phone VARCHAR(50),
    template_id VARCHAR(255),
    campaign_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_button_clicks_tenant_id ON button_clicks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_button_clicks_message_id ON button_clicks(message_id);

-- Verify tables were created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('message_events', 'button_clicks')
ORDER BY table_name;
