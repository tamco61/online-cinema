-- ClickHouse Initialization Script for Analytics

-- Create analytics database
CREATE DATABASE IF NOT EXISTS analytics;

-- Viewing Events Table (for streaming analytics)
CREATE TABLE IF NOT EXISTS analytics.viewing_events
(
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt64,
    movie_id UInt64,
    event_type Enum8('start' = 1, 'pause' = 2, 'resume' = 3, 'stop' = 4, 'complete' = 5),
    timestamp DateTime DEFAULT now(),
    position_seconds UInt32,
    duration_seconds UInt32,
    quality String,
    device_type String,
    country_code FixedString(2),
    city String,
    ip_address String,
    user_agent String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, movie_id, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- Search Events Table
CREATE TABLE IF NOT EXISTS analytics.search_events
(
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt64,
    search_query String,
    results_count UInt32,
    timestamp DateTime DEFAULT now(),
    clicked_movie_id Nullable(UInt64),
    click_position Nullable(UInt8)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- Movie Popularity Materialized View
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.movie_popularity_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, movie_id)
AS SELECT
    toDate(timestamp) AS date,
    movie_id,
    count() AS views_count,
    uniq(user_id) AS unique_viewers,
    avg(duration_seconds) AS avg_watch_duration
FROM analytics.viewing_events
WHERE event_type = 'complete'
GROUP BY date, movie_id;

-- User Activity Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.user_activity_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id)
AS SELECT
    toDate(timestamp) AS date,
    user_id,
    count() AS total_views,
    sum(duration_seconds) AS total_watch_time,
    uniq(movie_id) AS unique_movies_watched
FROM analytics.viewing_events
GROUP BY date, user_id;

-- Search Conversion Rate
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.search_conversion_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY hour
AS SELECT
    toStartOfHour(timestamp) AS hour,
    count() AS total_searches,
    countIf(clicked_movie_id IS NOT NULL) AS searches_with_click,
    countIf(clicked_movie_id IS NOT NULL) / count() AS conversion_rate
FROM analytics.search_events
GROUP BY hour;

-- Real-time Dashboard Query Examples (pre-aggregated)
CREATE TABLE IF NOT EXISTS analytics.realtime_metrics
(
    metric_name String,
    metric_value Float64,
    timestamp DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (metric_name, timestamp)
TTL timestamp + INTERVAL 7 DAY;

-- Payment Events
CREATE TABLE IF NOT EXISTS analytics.payment_events
(
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UInt64,
    amount Decimal(10, 2),
    currency FixedString(3),
    payment_method String,
    subscription_plan String,
    status Enum8('pending' = 1, 'completed' = 2, 'failed' = 3, 'refunded' = 4),
    timestamp DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp);

-- Revenue Analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.revenue_daily
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, subscription_plan)
AS SELECT
    toDate(timestamp) AS date,
    subscription_plan,
    currency,
    sum(amount) AS total_revenue,
    count() AS transaction_count,
    countIf(status = 'completed') AS successful_transactions,
    countIf(status = 'failed') AS failed_transactions
FROM analytics.payment_events
GROUP BY date, subscription_plan, currency;

-- Grant permissions
GRANT ALL ON analytics.* TO default;
