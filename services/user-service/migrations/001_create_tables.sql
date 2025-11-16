-- User Service Database Migration
-- Creates all tables: user_profiles, plans, subscriptions, watch_history, favorites

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Profiles
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL,  -- from auth-service
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    country VARCHAR(2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- Plans
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    interval VARCHAR(20) NOT NULL DEFAULT 'monthly',
    max_devices INTEGER NOT NULL DEFAULT 1,
    supports_hd BOOLEAN NOT NULL DEFAULT FALSE,
    supports_4k BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    cancelled_at TIMESTAMP,
    payment_reference VARCHAR(255),
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_profile_id ON subscriptions(profile_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Watch History
CREATE TABLE watch_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    content_id UUID NOT NULL,  -- from content-service
    content_type VARCHAR(20) NOT NULL,
    progress_seconds INTEGER NOT NULL DEFAULT 0,
    duration_seconds INTEGER,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    last_watched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_watch_history_profile_id ON watch_history(profile_id);
CREATE INDEX idx_watch_history_content_id ON watch_history(content_id);
CREATE INDEX idx_watch_history_last_watched ON watch_history(last_watched_at);

-- Favorites
CREATE TABLE favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    content_id UUID NOT NULL,  -- from content-service
    content_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profile_id, content_id)
);

CREATE INDEX idx_favorites_profile_id ON favorites(profile_id);
CREATE INDEX idx_favorites_content_id ON favorites(content_id);

-- Insert sample plans
INSERT INTO plans (name, description, price, currency, interval, max_devices, supports_hd, supports_4k) VALUES
('Basic', 'Basic plan with SD quality', 9.99, 'USD', 'monthly', 1, FALSE, FALSE),
('Standard', 'Standard plan with HD quality', 14.99, 'USD', 'monthly', 2, TRUE, FALSE),
('Premium', 'Premium plan with 4K quality', 19.99, 'USD', 'monthly', 4, TRUE, TRUE);
