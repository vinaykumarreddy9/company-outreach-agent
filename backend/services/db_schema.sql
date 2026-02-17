-- Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    product_description TEXT,
    value_proposition TEXT,
    key_offerings TEXT[],
    target_audience TEXT,
    strategic_positioning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'DRAFT' -- 'DRAFT', 'MONITORING_READY', 'MONITORING_ACTIVE', 'INACTIVE'
);

-- Target Companies Table
CREATE TABLE IF NOT EXISTS target_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id),
    name TEXT NOT NULL,
    website TEXT,
    description TEXT,
    relevance_score INTEGER,
    recent_news TEXT[],
    key_challenges TEXT[],
    strategic_priorities TEXT[],
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'DISCOVERY', 'TERMINATED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Decision Makers Table
CREATE TABLE IF NOT EXISTS decision_makers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id),
    company_id UUID REFERENCES target_companies(id),
    name TEXT NOT NULL,
    role TEXT,
    role_category TEXT,
    email TEXT,
    linkedin TEXT,
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'DISCOVERY', 'TERMINATED'
    turn_count INTEGER DEFAULT 0,
    last_outbound_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Emails Table
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_maker_id UUID REFERENCES decision_makers(id),
    sender TEXT,
    recipient TEXT,
    subject TEXT,
    body TEXT,
    status TEXT DEFAULT 'PENDING_APPROVAL', -- 'PENDING_APPROVAL', 'APPROVED', 'SENT', 'RECEIVED', 'DECLINED'
    direction TEXT, -- 'inbound', 'outbound'
    type TEXT, -- 'initial', 'reminder', 'reply'
    intent TEXT, -- 'POSITIVE', 'NEUTRAL', 'NEGATIVE'
    intent_confidence FLOAT,
    human_approved BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    message_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Event Log for Audit & Idempotency
CREATE TABLE IF NOT EXISTS event_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    entity_id UUID,
    entity_type TEXT, -- 'CAMPAIGN', 'COMPANY', 'DECISION_MAKER', 'EMAIL'
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled Emails (Legacy support or internal timer reference)
CREATE TABLE IF NOT EXISTS scheduled_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_maker_id UUID REFERENCES decision_makers(id),
    recipient_email TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'pending', 
    type TEXT,
    step INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
