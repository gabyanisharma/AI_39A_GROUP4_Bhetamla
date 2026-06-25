-- =========================================
-- CREATE DATABASE
-- =========================================

CREATE DATABASE IF NOT EXISTS bhetamla_db;
USE bhetamla_db;


-- =========================================
-- EMAIL VERIFICATION (helper comments)
-- =========================================
-- SET SQL_SAFE_UPDATES = 0;
-- UPDATE users SET is_verified = 1;
-- SET SQL_SAFE_UPDATES = 1;
-- SELECT id, email, is_verified FROM users;
-- UPDATE users SET is_verified = 0 WHERE email = 'testuser@example.com';


-- =========================================
-- USERS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),

    password_hash VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255) DEFAULT 'default.png',

    role ENUM('user', 'admin') DEFAULT 'user',

    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_token_expiry DATETIME,

    reset_token VARCHAR(255),
    reset_token_expiry DATETIME,

    budget_preference DECIMAL(10,2) DEFAULT 0 CHECK (budget_preference >= 0),

    cuisine_preference VARCHAR(255),

    transport_preference VARCHAR(50) DEFAULT 'any',

    theme_preference ENUM('light', 'dark') DEFAULT 'light',

    language_preference ENUM('en', 'np') DEFAULT 'en',

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- =========================================
-- SAVED PLACES
-- =========================================

CREATE TABLE IF NOT EXISTS saved_places (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    place_name VARCHAR(255) NOT NULL,
    address VARCHAR(255),

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);


-- =========================================
-- EMERGENCY CONTACTS
-- =========================================

CREATE TABLE IF NOT EXISTS emergency_contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    relationship VARCHAR(50),
    email VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);


-- =========================================
-- SOS ALERTS
-- =========================================

CREATE TABLE IF NOT EXISTS sos_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    message TEXT,

    status ENUM('active', 'cancelled', 'resolved') DEFAULT 'active',

    cancel_pin VARCHAR(10),

    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP NULL,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);


-- =========================================
-- FRIENDS
-- =========================================

CREATE TABLE IF NOT EXISTS friends (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    friend_id INT NOT NULL,

    status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    FOREIGN KEY (friend_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    UNIQUE KEY unique_friendship (user_id, friend_id),

    CHECK (user_id <> friend_id)
);


-- =========================================
-- AVAILABILITY SLOTS
-- =========================================

CREATE TABLE IF NOT EXISTS availability_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    date DATE NOT NULL,

    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    label VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    CHECK (start_time < end_time)
);


-- =========================================
-- MEETUP SCHEDULES
-- =========================================

CREATE TABLE IF NOT EXISTS meetup_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,

    organizer_id INT NOT NULL,

    title VARCHAR(255) NOT NULL,
    description TEXT,

    proposed_date DATE NOT NULL,
    proposed_time TIME NOT NULL,

    status ENUM('pending', 'confirmed', 'cancelled') DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (organizer_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);


-- =========================================
-- SCHEDULE INVITES
-- =========================================

CREATE TABLE IF NOT EXISTS schedule_invites (
    id INT AUTO_INCREMENT PRIMARY KEY,

    schedule_id INT NOT NULL,
    user_id INT NOT NULL,

    status ENUM('pending', 'accepted', 'declined') DEFAULT 'pending',

    responded_at TIMESTAMP NULL,

    FOREIGN KEY (schedule_id)
    REFERENCES meetup_schedules(id)
    ON DELETE CASCADE,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    UNIQUE KEY unique_schedule_invite (schedule_id, user_id)
);


-- =========================================
-- NOTIFICATIONS
-- =========================================

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    type ENUM(
        'meetup',
        'friend',
        'reminder',
        'sos',
        'general'
    ) DEFAULT 'general',

    is_read BOOLEAN DEFAULT FALSE,

    read_at TIMESTAMP NULL,

    link VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
);


-- =========================================
-- MEETUPS
-- =========================================

CREATE TABLE IF NOT EXISTS meetups (
    id INT AUTO_INCREMENT PRIMARY KEY,

    group_id INT,

    title VARCHAR(255) NOT NULL,
    description TEXT,

    created_by INT NOT NULL,

    status ENUM('planned', 'active', 'completed', 'cancelled') DEFAULT 'planned',

    midpoint_lat DECIMAL(10,8),
    midpoint_lng DECIMAL(11,8),
    midpoint_address VARCHAR(255),

    meetup_date DATE,
    meetup_time TIME,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
    REFERENCES users(id)
    ON DELETE CASCADE
);


-- =========================================
-- MEETUP MEMBERS
-- =========================================

CREATE TABLE IF NOT EXISTS meetup_members (
    id INT AUTO_INCREMENT PRIMARY KEY,

    meetup_id INT NOT NULL,
    user_id INT NOT NULL,

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    address VARCHAR(255),

    status ENUM('invited', 'accepted', 'declined') DEFAULT 'invited',

    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (meetup_id)
    REFERENCES meetups(id)
    ON DELETE CASCADE,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    UNIQUE KEY unique_member (meetup_id, user_id)
);


-- =========================================
-- MEETUP ROUTES
-- =========================================

CREATE TABLE IF NOT EXISTS meetup_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,

    meetup_id INT NOT NULL,
    created_by INT NOT NULL,

    travel_mode ENUM('driving', 'walking', 'cycling') DEFAULT 'driving',

    distance_m INT,
    duration_s INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (meetup_id)
    REFERENCES meetups(id)
    ON DELETE CASCADE,

    FOREIGN KEY (created_by)
    REFERENCES users(id)
    ON DELETE CASCADE,

    UNIQUE KEY unique_meetup_route (meetup_id)
);


-- =========================================
-- MEETUP ROUTE WAYPOINTS
-- =========================================

CREATE TABLE IF NOT EXISTS meetup_route_waypoints (
    id INT AUTO_INCREMENT PRIMARY KEY,

    route_id INT NOT NULL,
    sequence_index INT NOT NULL,

    label VARCHAR(100) NOT NULL,
    address VARCHAR(255),

    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,

    source ENUM('geocoder', 'map_click', 'manual', 'dragged') DEFAULT 'manual',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (route_id)
    REFERENCES meetup_routes(id)
    ON DELETE CASCADE,

    UNIQUE KEY unique_route_sequence (route_id, sequence_index)
);


-- =========================================
-- PLACE SUGGESTIONS
-- =========================================

CREATE TABLE IF NOT EXISTS place_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,

    meetup_id INT NOT NULL,

    place_name VARCHAR(255) NOT NULL,
    address VARCHAR(255),

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    rating DECIMAL(3,2),

    suggested_by INT,

    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (meetup_id)
    REFERENCES meetups(id)
    ON DELETE CASCADE,

    FOREIGN KEY (suggested_by)
    REFERENCES users(id)
    ON DELETE SET NULL
);


-- =========================================
-- RESTAURANTS
-- (defined before restaurant_offers so FK works)
-- =========================================

CREATE TABLE IF NOT EXISTS restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(255) NOT NULL,
    description TEXT,
    address VARCHAR(255),

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    category VARCHAR(100),
    cuisine VARCHAR(100),

    price_range ENUM('budget', 'mid', 'expensive') DEFAULT 'mid',
    avg_cost_per_person DECIMAL(10,2),

    rating DECIMAL(3,2) DEFAULT 0,
    review_count INT DEFAULT 0,

    ambience VARCHAR(100),
    image_url VARCHAR(255),
    thumbnail_url VARCHAR(255),

    opening_time TIME,
    closing_time TIME,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_restaurant_name (name)
);


-- =========================================
-- RESTAURANT REVIEWS
-- =========================================

CREATE TABLE IF NOT EXISTS restaurant_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,

    restaurant_id INT NOT NULL,
    user_id INT NOT NULL,

    rating DECIMAL(3,2) NOT NULL,
    review TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (restaurant_id)
    REFERENCES restaurants(id)
    ON DELETE CASCADE,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    UNIQUE KEY unique_review (restaurant_id, user_id)
);


-- =========================================
-- RESTAURANT OFFERS
-- =========================================

CREATE TABLE IF NOT EXISTS restaurant_offers (
    id INT AUTO_INCREMENT PRIMARY KEY,

    restaurant_id INT NOT NULL,

    title VARCHAR(100) NOT NULL,
    description TEXT,
    discount_percent INT DEFAULT 0,

    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (restaurant_id)
    REFERENCES restaurants(id)
    ON DELETE CASCADE,

    UNIQUE KEY uq_offer_restaurant_title (restaurant_id, title)
);


-- =========================================
-- USER SAVED OFFERS
-- =========================================

CREATE TABLE IF NOT EXISTS user_saved_offers (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    offer_id INT NOT NULL,

    remind_me BOOLEAN DEFAULT FALSE,

    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,

    FOREIGN KEY (offer_id)
    REFERENCES restaurant_offers(id)
    ON DELETE CASCADE,

    UNIQUE KEY idx_user_offer (user_id, offer_id)
);


-- =========================================
-- RIDE ESTIMATES
-- =========================================

CREATE TABLE IF NOT EXISTS ride_estimates (
    id INT AUTO_INCREMENT PRIMARY KEY,

    meetup_id INT NOT NULL,
    user_id INT NOT NULL,

    from_lat DECIMAL(10,8),
    from_lng DECIMAL(11,8),
    from_address VARCHAR(255),

    to_lat DECIMAL(10,8),
    to_lng DECIMAL(11,8),
    to_address VARCHAR(255),

    distance_km DECIMAL(8,3),

    pathao_bike_cost DECIMAL(10,2),
    pathao_car_cost  DECIMAL(10,2),
    taxi_cost        DECIMAL(10,2),
    walk_minutes     INT,
    bike_minutes     INT,
    car_minutes      INT,

    is_peak_hour BOOLEAN DEFAULT FALSE,

    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (meetup_id)
        REFERENCES meetups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)
        REFERENCES users(id)  ON DELETE CASCADE,

    UNIQUE KEY unique_ride_estimate (meetup_id, user_id)
);


-- ============================================================
-- FARE DROP ALERT FEATURE
-- ============================================================

-- Travel Estimate
CREATE TABLE IF NOT EXISTS travel_estimate (
    travelID      INT AUTO_INCREMENT PRIMARY KEY,
    meetupID      INT NOT NULL,
    userID        INT NOT NULL,
    mode          ENUM('car','bike','public','walk') NOT NULL DEFAULT 'car',
    travelTime    INT COMMENT 'minutes',
    distance      DECIMAL(8,2) COMMENT 'km',
    estimatedCost DECIMAL(10,2),
    createdAt     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meetupID) REFERENCES meetups(id) ON DELETE CASCADE,
    FOREIGN KEY (userID)   REFERENCES users(id)   ON DELETE CASCADE
);

-- Fare Alert subscriptions
CREATE TABLE IF NOT EXISTS fare_alert (
    alertID       INT AUTO_INCREMENT PRIMARY KEY,
    userID        INT NOT NULL,
    meetupID      INT NOT NULL,
    mode          ENUM('car','bike','public','walk') NOT NULL DEFAULT 'car',
    targetFare    DECIMAL(10,2) NOT NULL COMMENT 'Alert when fare drops to or below this',
    currentFare   DECIMAL(10,2)           COMMENT 'Last checked fare',
    isActive      TINYINT(1) DEFAULT 1,
    isTriggered   TINYINT(1) DEFAULT 0    COMMENT '1 once the alert has fired',
    createdAt     DATETIME DEFAULT CURRENT_TIMESTAMP,
    triggeredAt   DATETIME,
    FOREIGN KEY (userID)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (meetupID) REFERENCES meetups(id) ON DELETE CASCADE
);

-- Fare price history (powers sparkline chart)
CREATE TABLE IF NOT EXISTS fare_history (
    historyID     INT AUTO_INCREMENT PRIMARY KEY,
    meetupID      INT NOT NULL,
    mode          ENUM('car','bike','public','walk') NOT NULL,
    fare          DECIMAL(10,2) NOT NULL,
    recordedAt    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meetupID) REFERENCES meetups(id) ON DELETE CASCADE
);


-- =========================================
-- SAVED ROUTES (Multi-Stop Route Planning)
-- =========================================

CREATE TABLE IF NOT EXISTS saved_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    route_name VARCHAR(255) NOT NULL DEFAULT 'My Route',

    -- JSON array: [{name, lat, lng}, ...]
    waypoints_json TEXT NOT NULL,

    -- Optimized by 'time' or 'distance'
    optimize_by VARCHAR(20) DEFAULT 'time',

    total_distance_km DECIMAL(8,2) DEFAULT 0,
    total_duration_min INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================
-- TRENDING MEETUP SPOTS (Explore Feed)
-- =========================================

CREATE TABLE IF NOT EXISTS trending_spots (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(255) NOT NULL,
    description TEXT,
    address VARCHAR(255),

    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),

    category VARCHAR(100),
    cuisine VARCHAR(100),
    ambience VARCHAR(100),

    price_range ENUM('budget', 'mid', 'expensive') DEFAULT 'mid',
    avg_cost_per_person DECIMAL(10,2),

    rating DECIMAL(3,2) DEFAULT 0,
    review_count INT DEFAULT 0,
    trend_score DECIMAL(5,2) DEFAULT 0,

    image_url VARCHAR(255),
    thumbnail_url VARCHAR(255),

    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================================
-- USER SPOT INTERACTIONS
-- =========================================

CREATE TABLE IF NOT EXISTS user_spot_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    spot_id INT NOT NULL,

    interaction_type ENUM('view', 'like', 'save', 'share', 'visit') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (spot_id) REFERENCES trending_spots(id) ON DELETE CASCADE,

    UNIQUE KEY unique_user_spot_interaction (user_id, spot_id, interaction_type)
);

-- =========================================
-- SPOT RECOMMENDATIONS
-- =========================================

CREATE TABLE IF NOT EXISTS spot_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    spot_id INT NOT NULL,
    recommended_by INT,
    recommendation_reason VARCHAR(255),
    score DECIMAL(5,2) DEFAULT 0,

    is_dismissed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (spot_id) REFERENCES trending_spots(id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_by) REFERENCES users(id) ON DELETE SET NULL,

    UNIQUE KEY unique_user_spot_recommendation (user_id, spot_id)
);

-- =========================================
-- SMART NOTIFICATION ALERTS
-- =========================================

CREATE TABLE IF NOT EXISTS notification_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    -- Master switch for smart alerts.
    smart_alerts_enabled BOOLEAN DEFAULT TRUE,

    -- Per-category toggles.
    meetup_reminders BOOLEAN DEFAULT TRUE,
    invite_alerts BOOLEAN DEFAULT TRUE,
    trending_alerts BOOLEAN DEFAULT TRUE,

    -- How many hours before a meetup to fire the reminder.
    reminder_lead_hours INT DEFAULT 24,

    -- Quiet hours on a 24h clock - alerts in this window are suppressed.
    quiet_hours_start TINYINT NULL,
    quiet_hours_end TINYINT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    UNIQUE KEY unique_user_pref (user_id)
);

-- Idempotency log so the smart-alert engine never fires the same alert twice.
CREATE TABLE IF NOT EXISTS smart_alert_log (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    alert_key VARCHAR(191) NOT NULL,
    notification_id INT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    UNIQUE KEY unique_user_alert (user_id, alert_key)
);

-- Indexes for fast lookups are created conditionally in app/database.py

CREATE TABLE IF NOT EXISTS meetup_plan_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    meetup_id INT NOT NULL,
    user_id INT NOT NULL,
    cuisine VARCHAR(100),
    budget_min INT DEFAULT 200,
    budget_max INT DEFAULT 2000,
    ambience VARCHAR(100),
    selected_venue VARCHAR(255),
    selected_venue_lat DECIMAL(10,8),
    selected_venue_lng DECIMAL(11,8),
    ride_option VARCHAR(100),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (meetup_id) REFERENCES meetups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_pref (meetup_id, user_id)
);
-- =========================================
-- BUDGET SPLIT RECORDS
-- Append to schema.sql after meetup_plan_preferences
--
-- One canonical split row per meetup.
-- record_budget_split() upserts on uq_bsr_meetup so calling
-- "Send Split" multiple times is safe.
-- recorded_by tracks the last user who pushed the button.
-- badge_hint 'penny_pincher' is returned to the client on success.
-- =========================================
 
CREATE TABLE IF NOT EXISTS budget_split_records (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
 
    meetup_id           INT          NOT NULL,
    recorded_by         INT          NOT NULL,
 
    total_bill          DECIMAL(10,2) DEFAULT 0
                            CHECK (total_bill >= 0),
 
    member_count        INT           DEFAULT 1
                            CHECK (member_count > 0),
 
    per_person_amount   DECIMAL(10,2) DEFAULT 0
                            CHECK (per_person_amount >= 0),
 
    -- Snapshot of the modal summary line,
    -- e.g. "Equal split: NPR 1,167 / person"
    split_summary       VARCHAR(255),
 
    recorded_at         DATETIME      DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,
 
    FOREIGN KEY (meetup_id)
        REFERENCES meetups(id)  ON DELETE CASCADE,
 
    FOREIGN KEY (recorded_by)
        REFERENCES users(id)    ON DELETE CASCADE,
 
    -- One canonical split per meetup.
    -- The upsert in record_budget_split() keeps this in sync.
    UNIQUE KEY uq_bsr_meetup (meetup_id)
);

-- =========================================
-- APP RATING & FEEDBACK (US27)
-- General product feedback with a 1–5 star
-- rating and an optional message.
-- =========================================
CREATE TABLE IF NOT EXISTS app_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    rating TINYINT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_feedback_user (user_id, created_at)
);

-- =========================================
-- CALENDAR SYNC (US29)
-- In-app calendar connections plus imported
-- .ics events for conflict detection.
-- =========================================
CREATE TABLE IF NOT EXISTS calendar_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider ENUM('google', 'outlook', 'apple', 'other') DEFAULT 'other',
    account_email VARCHAR(190) NOT NULL,
    display_name VARCHAR(190),
    permission_scope ENUM('read', 'write', 'read_write') DEFAULT 'read_write',
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_calendar_account (user_id, account_email),
    INDEX idx_calendar_accounts_user_active (user_id, is_active)
);

CREATE TABLE IF NOT EXISTS imported_calendar_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    external_uid VARCHAR(191) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    starts_at DATETIME NOT NULL,
    ends_at DATETIME NOT NULL,
    is_all_day BOOLEAN DEFAULT FALSE,
    source ENUM('ics_upload', 'manual_sync') DEFAULT 'ics_upload',
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES calendar_accounts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_account_external_event (account_id, external_uid),
    INDEX idx_imported_events_user_time (user_id, starts_at, ends_at)
);


-- =========================================
-- FRIEND GROUPS (Group Chat feature)
-- =========================================

CREATE TABLE IF NOT EXISTS friend_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name     VARCHAR(255) NOT NULL,
    owner_id INT          NOT NULL,
    is_chat_group BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- =========================================
-- FRIEND GROUP MEMBERS
-- =========================================

CREATE TABLE IF NOT EXISTS friend_group_members (
    id INT AUTO_INCREMENT PRIMARY KEY,

    group_id INT NOT NULL,
    user_id  INT NOT NULL,

    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (group_id)
        REFERENCES friend_groups(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_group_member (group_id, user_id)
) ENGINE=InnoDB;


-- =========================================
-- GROUP CHAT MESSAGES
-- =========================================

CREATE TABLE IF NOT EXISTS group_chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,

    group_id INT NOT NULL,
    user_id  INT NOT NULL,

    body       TEXT    NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (group_id)
        REFERENCES friend_groups(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_gcm_group_created (group_id, created_at)
) ENGINE=InnoDB;


-- =========================================
-- GROUP CHAT READ RECEIPTS
-- =========================================

CREATE TABLE IF NOT EXISTS group_chat_reads (
    id INT AUTO_INCREMENT PRIMARY KEY,

    message_id INT NOT NULL,
    user_id    INT NOT NULL,

    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (message_id)
        REFERENCES group_chat_messages(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_chat_read (message_id, user_id)
) ENGINE=InnoDB;


-- =========================================
-- GROUP CHAT TYPING INDICATORS
-- =========================================

CREATE TABLE IF NOT EXISTS group_chat_typing (
    group_id INT NOT NULL,
    user_id  INT NOT NULL,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (group_id, user_id),

    FOREIGN KEY (group_id)
        REFERENCES friend_groups(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- =========================================
-- VENUE VOTES (Group Voting)
-- =========================================

CREATE TABLE IF NOT EXISTS venue_votes (
    id INT AUTO_INCREMENT PRIMARY KEY,

    meetup_id  INT NOT NULL,
    created_by INT NOT NULL,

    deadline DATETIME NOT NULL,
    status   ENUM('open', 'closed', 'draw') NOT NULL DEFAULT 'open',

    winner_option_id INT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (meetup_id)
        REFERENCES meetups(id)
        ON DELETE CASCADE,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_venue_votes_meetup_status (meetup_id, status)
) ENGINE=InnoDB;


-- =========================================
-- VENUE VOTE OPTIONS
-- =========================================

CREATE TABLE IF NOT EXISTS venue_vote_options (
    id INT AUTO_INCREMENT PRIMARY KEY,

    vote_id       INT          NOT NULL,
    restaurant_id INT          NULL,

    label   VARCHAR(255) NOT NULL,
    address VARCHAR(255),

    FOREIGN KEY (vote_id)
        REFERENCES venue_votes(id)
        ON DELETE CASCADE,

    FOREIGN KEY (restaurant_id)
        REFERENCES restaurants(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;


-- =========================================
-- VENUE VOTE CASTS
-- =========================================

CREATE TABLE IF NOT EXISTS venue_vote_casts (
    id INT AUTO_INCREMENT PRIMARY KEY,

    vote_id   INT NOT NULL,
    user_id   INT NOT NULL,
    option_id INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vote_id)
        REFERENCES venue_votes(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (option_id)
        REFERENCES venue_vote_options(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_vote_cast (vote_id, user_id)
) ENGINE=InnoDB;


-- =========================================
-- MEETUP GALLERY PHOTOS
-- =========================================

CREATE TABLE IF NOT EXISTS meetup_gallery (
    id INT AUTO_INCREMENT PRIMARY KEY,

    meetup_id INT          NOT NULL,
    user_id   INT          NOT NULL,

    file_path VARCHAR(255) NOT NULL,
    caption   VARCHAR(500) DEFAULT '',
    is_public BOOLEAN      NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (meetup_id)
        REFERENCES meetups(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_gallery_meetup (meetup_id, created_at)
) ENGINE=InnoDB;


-- =========================================
-- GALLERY LIKES
-- =========================================

CREATE TABLE IF NOT EXISTS gallery_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,

    gallery_id INT NOT NULL,
    user_id    INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (gallery_id)
        REFERENCES meetup_gallery(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_gallery_like (gallery_id, user_id)
) ENGINE=InnoDB;


-- =========================================
-- GALLERY COMMENTS
-- =========================================

CREATE TABLE IF NOT EXISTS gallery_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,

    gallery_id INT  NOT NULL,
    user_id    INT  NOT NULL,

    comment    TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (gallery_id)
        REFERENCES meetup_gallery(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    INDEX idx_gallery_comments_gallery (gallery_id, created_at)
) ENGINE=InnoDB;


-- =========================================
-- BUDGET SPLIT LOG
-- (tracks each call to record_budget_split)
-- =========================================

CREATE TABLE IF NOT EXISTS budget_split_log (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id   INT NOT NULL,
    meetup_id INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (meetup_id)
        REFERENCES meetups(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- =========================================
-- SEED DATA: KATHMANDU RESTAURANTS
-- ~100 real restaurants across the valley.
-- Uses INSERT IGNORE so re-importing is safe.
-- =========================================

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Fire and Ice Pizzeria','Tridevi Marg, Thamel',27.7148,85.3128,'Restaurant','Italian','mid',4.5,412,'lively','11:00:00','22:00:00','Wood-fired pizzas and a buzzing crowd in central Thamel.',950,TRUE),
('Third Eye Restaurant','Chaksibari Marg, Thamel',27.7141,85.3110,'Restaurant','Indian','mid',4.3,198,'casual','11:00:00','22:30:00','Long-running Indian and Nepali kitchen popular with travellers.',850,TRUE),
('Yangling Tibetan Restaurant','Mandala Street, Thamel',27.7156,85.3116,'Restaurant','Tibetan','budget',4.4,263,'casual','08:00:00','21:30:00','Famous for hearty momos and thukpa at honest prices.',500,TRUE),
('La Dolce Vita','Thamel Marg, Thamel',27.7159,85.3122,'Restaurant','Italian','mid',4.4,176,'romantic','12:00:00','22:00:00','Cosy Italian trattoria with house-made pasta.',1100,TRUE),
('Pumpernickel Bakery','Chaksibari Marg, Thamel',27.7138,85.3113,'Cafe','Bakery','budget',4.2,154,'garden','07:00:00','20:00:00','Garden bakery cafe great for breakfast meetups.',450,TRUE),
('Or2K Cushion Lounge','Mandala Street, Thamel',27.7152,85.3120,'Restaurant','Mediterranean','mid',4.3,221,'cozy','09:00:00','22:00:00','Vegetarian mezze on floor cushions, relaxed vibe.',900,TRUE),
('Decode Yoga & Cafe','Saat Ghumti, Thamel',27.7162,85.3105,'Cafe','Cafe','mid',4.5,97,'quiet','07:30:00','20:30:00','Calm wellness cafe with healthy bowls and coffee.',600,TRUE),
('New Orleans Cafe','Jyatha, Thamel',27.7128,85.3134,'Restaurant','Continental','mid',4.3,188,'lively','10:00:00','23:00:00','Courtyard restaurant with live music nights.',1000,TRUE),
('Roadhouse Cafe Thamel','Jyatha, Thamel',27.7126,85.3137,'Restaurant','Italian','mid',4.4,209,'casual','10:00:00','22:30:00','Wood-fired pizza branch tucked off the main strip.',1100,TRUE),
('Cafe Mitra','Chaksibari Marg, Thamel',27.7144,85.3108,'Restaurant','Continental','expensive',4.6,132,'romantic','12:00:00','22:00:00','Intimate fine-dining spot with curated wine list.',1900,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Hankook Sarang','Durbar Marg, Kathmandu',27.7115,85.3175,'Restaurant','Korean','mid',4.4,168,'casual','11:00:00','22:00:00','Authentic Korean BBQ in the heart of the city.',1300,TRUE),
('Chez Caroline','Babar Mahal Revisited',27.6985,85.3265,'Restaurant','French','expensive',4.6,211,'garden','09:00:00','22:00:00','European bistro in a heritage courtyard.',1800,TRUE),
('K-Too Beer & Steakhouse','Durbar Marg, Kathmandu',27.7108,85.3178,'Restaurant','Steakhouse','expensive',4.5,240,'lively','11:00:00','23:00:00','Steaks, burgers and cold beer near the palace.',1700,TRUE),
('The Ship Restaurant','Kamaladi, Kathmandu',27.7060,85.3220,'Restaurant','Continental','mid',4.2,143,'lively','11:00:00','22:30:00','Nautical-themed bar and grill for big groups.',1100,TRUE),
('Bota Momo Durbar Marg','Durbar Marg, Kathmandu',27.7120,85.3182,'Restaurant','Nepali','budget',4.3,320,'casual','10:00:00','21:00:00','Steamed and jhol momos, always a queue.',400,TRUE),
('Java House Durbar Marg','Durbar Marg, Kathmandu',27.7112,85.3179,'Cafe','Coffee','mid',4.4,287,'lively','07:00:00','21:00:00','Flagship coffee house, a classic meeting point.',650,TRUE),
('Wunjala Moskva','Naxal, Kathmandu',27.7170,85.3275,'Restaurant','Nepali','expensive',4.5,121,'garden','12:00:00','22:00:00','Newari and Russian fusion in a leafy garden.',1600,TRUE),
('1905 Suites & Restaurant','Kantipath, Lazimpat',27.7185,85.3185,'Restaurant','Continental','mid',4.4,176,'garden','08:00:00','22:00:00','Heritage lawn cafe hosting weekend markets.',1200,TRUE),
('Tamarind Restaurant','Lazimpat, Kathmandu',27.7225,85.3205,'Restaurant','Continental','mid',4.3,154,'garden','08:00:00','22:00:00','Garden dining with a broad continental menu.',1100,TRUE),
('Or-Tho Restaurant','Lazimpat, Kathmandu',27.7231,85.3212,'Restaurant','Korean','mid',4.2,98,'casual','11:00:00','21:30:00','Homestyle Korean meals near the embassies.',1000,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Cafe Cheeno','Lazimpat, Kathmandu',27.7218,85.3208,'Cafe','Cafe','mid',4.5,142,'cozy','07:30:00','21:00:00','Brunch-friendly cafe with strong espresso.',700,TRUE),
('Roadhouse Cafe Bhatbhateni','Bhatbhateni, Kathmandu',27.7221,85.3305,'Restaurant','Italian','mid',4.4,233,'casual','10:00:00','22:30:00','Reliable pizza and pasta beside the supermarket.',1100,TRUE),
('Bawarchi Restaurant','Naxal, Kathmandu',27.7158,85.3282,'Restaurant','Indian','mid',4.3,167,'family_friendly','11:00:00','22:00:00','North Indian curries and biryani for groups.',900,TRUE),
('Cafe Swotha','Naxal, Kathmandu',27.7162,85.3278,'Cafe','Cafe','mid',4.4,112,'quiet','08:00:00','20:30:00','Quiet courtyard cafe for catch-ups.',650,TRUE),
('Sajha Chiya Ghar','Baluwatar, Kathmandu',27.7282,85.3288,'Cafe','Cafe','budget',4.2,89,'casual','07:00:00','20:00:00','Local tea house with snacks and milk tea.',300,TRUE),
('Imago Dei Cafe','Naxal, Kathmandu',27.7150,85.3290,'Cafe','Cafe','mid',4.5,76,'quiet','08:00:00','20:00:00','Art-gallery cafe, calm and creative.',700,TRUE),
('Le Trio Restaurant','Maharajgunj, Kathmandu',27.7382,85.3292,'Restaurant','Continental','expensive',4.5,143,'fine_dining','11:00:00','22:30:00','Upscale continental kitchen near the hospital.',1900,TRUE),
('Chabahil Sekuwa Corner','Chabahil, Kathmandu',27.7178,85.3470,'Restaurant','Nepali','budget',4.2,256,'lively','16:00:00','23:00:00','Smoky grilled sekuwa and chilled drinks.',600,TRUE),
('Garden Kitchen Boudha','Boudha, Kathmandu',27.7215,85.3622,'Restaurant','Continental','mid',4.4,167,'garden','08:00:00','22:00:00','Stupa-view garden restaurant, relaxed afternoons.',1000,TRUE),
('Flavors Cafe Boudha','Boudha, Kathmandu',27.7208,85.3615,'Cafe','Cafe','mid',4.5,142,'rooftop','07:00:00','21:00:00','Rooftop cafe overlooking the great stupa.',650,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Utse Tibetan Restaurant','Boudha, Kathmandu',27.7220,85.3608,'Restaurant','Tibetan','budget',4.3,188,'casual','08:00:00','21:30:00','Classic Tibetan dishes near the kora.',550,TRUE),
('Stupa View Restaurant','Boudha, Kathmandu',27.7218,85.3612,'Restaurant','Vegetarian','mid',4.5,173,'rooftop','09:00:00','21:30:00','Vegetarian terrace dining facing the stupa.',1100,TRUE),
('The Yellow House','Sanepa, Lalitpur',27.6812,85.3078,'Cafe','Cafe','mid',4.6,211,'garden','07:30:00','21:00:00','Bright garden cafe loved for brunch.',800,TRUE),
('Cafe Soma Jhamel','Jhamsikhel, Lalitpur',27.6759,85.3145,'Cafe','Cafe','mid',4.5,198,'cozy','07:30:00','21:30:00','Leafy courtyard for long catch-ups.',700,TRUE),
('Heritage Kitchen & Bar','Jhamsikhel, Lalitpur',27.6762,85.3150,'Restaurant','Continental','mid',4.4,165,'lively','11:00:00','23:00:00','Bar and grill at the heart of Jhamel.',1200,TRUE),
('Bajeko Sekuwa Jhamsikhel','Jhamsikhel, Lalitpur',27.6755,85.3138,'Restaurant','Nepali','mid',4.3,287,'family_friendly','11:00:00','22:00:00','Famous Nepali grill chain, generous portions.',850,TRUE),
('Sing Ma Food Court','Jhamsikhel, Lalitpur',27.6766,85.3148,'Restaurant','Chinese','budget',4.2,176,'casual','11:00:00','21:30:00','Hand-pulled noodles and dumplings.',600,TRUE),
('The Tap House','Jhamsikhel, Lalitpur',27.6758,85.3152,'Restaurant','Continental','mid',4.4,221,'lively','12:00:00','23:00:00','Craft beer bar with pub food and big screens.',1100,TRUE),
('Cafe Du Temple Patan','Pulchowk, Lalitpur',27.6792,85.3168,'Restaurant','Continental','mid',4.3,134,'garden','08:00:00','22:00:00','Garden dining a short walk from Patan square.',1000,TRUE),
('Karma Coffee Roasters','Jhamsikhel, Lalitpur',27.6760,85.3140,'Cafe','Coffee','budget',4.5,152,'quiet','07:30:00','20:00:00','Specialty roaster, laptop-friendly mornings.',500,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('The Village Cafe','Pulchowk, Lalitpur',27.6795,85.3172,'Restaurant','Nepali','mid',4.4,167,'family_friendly','11:00:00','21:30:00','Community cafe serving authentic Newari thali.',800,TRUE),
('Dhokaima Cafe','Patan Dhoka, Lalitpur',27.6748,85.3215,'Restaurant','Continental','mid',4.5,198,'garden','08:00:00','22:00:00','Garden restaurant in a restored Newari home.',1100,TRUE),
('The Old House Riverside','Jhamsikhel, Lalitpur',27.6746,85.3122,'Restaurant','Continental','expensive',4.6,256,'lively','12:00:00','23:00:00','Riverside lounge with live music nights.',1800,TRUE),
('Jawalakhel Bara House','Jawalakhel, Lalitpur',27.6722,85.3112,'Restaurant','Newari','budget',4.3,213,'casual','08:00:00','20:00:00','Crispy wo (bara) and chatamari done right.',400,TRUE),
('Sasa Mama Pulchowk','Pulchowk, Lalitpur',27.6788,85.3175,'Restaurant','Tibetan','budget',4.4,264,'casual','10:00:00','21:00:00','Beloved local momo and noodle spot.',450,TRUE),
('Cafe de Patan','Mangal Bazar, Patan',27.6735,85.3248,'Cafe','Cafe','mid',4.5,187,'cozy','08:00:00','21:00:00','Heritage cafe steps from Patan Durbar Square.',700,TRUE),
('Museum Cafe Patan','Patan Museum, Patan',27.6740,85.3258,'Cafe','Continental','mid',4.6,165,'garden','09:00:00','18:00:00','Tranquil garden cafe inside the museum grounds.',900,TRUE),
('The Inn Patan','Mangal Bazar, Patan',27.6731,85.3252,'Restaurant','Continental','mid',4.3,121,'rooftop','09:00:00','21:30:00','Rooftop dining over the temple square.',1000,TRUE),
('Honacha Newari Restaurant','Patan Durbar Square',27.6728,85.3245,'Restaurant','Newari','budget',4.4,298,'casual','10:00:00','20:00:00','Iconic smoky Newari eatery off the square.',350,TRUE),
('Snowman Cafe','Freak Street, Basantapur',27.7022,85.3078,'Cafe','Bakery','budget',4.3,176,'cozy','08:00:00','20:00:00','Old-school cafe famous for chocolate cake.',400,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Newari Khaja Ghar Ason','Ason, Kathmandu',27.7068,85.3102,'Restaurant','Newari','budget',4.4,234,'casual','09:00:00','20:00:00','Bustling traditional snack house in old town.',350,TRUE),
('Bhojan Griha Heritage','Dillibazar, Kathmandu',27.7072,85.3280,'Restaurant','Nepali','expensive',4.5,211,'fine_dining','11:00:00','22:00:00','Cultural dining in a restored Rana mansion.',1800,TRUE),
('Krishnarpan Fine Dining','Battisputali, Kathmandu',27.7048,85.3492,'Restaurant','Nepali','expensive',4.7,121,'fine_dining','18:00:00','22:00:00','Multi-course Nepali tasting menu.',3500,TRUE),
('Gaushala Thakali Kitchen','Gaushala, Kathmandu',27.7095,85.3445,'Restaurant','Thakali','mid',4.4,176,'family_friendly','10:00:00','21:30:00','Authentic Thakali set with refills.',650,TRUE),
('Roadhouse Cafe Sanepa','Sanepa, Lalitpur',27.6818,85.3082,'Restaurant','Italian','mid',4.4,187,'casual','10:00:00','22:30:00','Sanepa branch with garden seating.',1100,TRUE),
('Local Project Cafe','Sanepa, Lalitpur',27.6822,85.3088,'Cafe','Cafe','mid',4.5,143,'cozy','08:00:00','21:00:00','Trendy cafe with brunch and specialty coffee.',750,TRUE),
('The Workshop Eatery','Kupondole, Lalitpur',27.6848,85.3158,'Restaurant','Continental','mid',4.5,165,'lively','11:00:00','23:00:00','Industrial-chic eatery with craft cocktails.',1300,TRUE),
('Newa Lahana','Kirtipur, Kathmandu',27.6790,85.2780,'Restaurant','Newari','mid',4.5,232,'family_friendly','11:00:00','21:00:00','Authentic Newari feast with cultural views.',800,TRUE),
('Trisara Garden Lazimpat','Lazimpat, Kathmandu',27.7228,85.3215,'Restaurant','Nepali','mid',4.5,188,'garden','12:00:00','22:00:00','Open courtyard Newari restaurant.',1300,TRUE),
('Places Rooftop Thamel','Thamel, Kathmandu',27.7160,85.3112,'Restaurant','Continental','mid',4.4,142,'rooftop','11:00:00','23:00:00','Skyline rooftop popular for group hangouts.',1100,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Le Sherpa Restaurant','Lazimpat, Kathmandu',27.7340,85.3275,'Restaurant','Continental','expensive',4.6,244,'garden','08:00:00','22:00:00','Farm-to-table garden venue and weekend market.',2000,TRUE),
('Newa Chhen Restaurant','Patan, Lalitpur',27.6738,85.3242,'Restaurant','Newari','mid',4.5,198,'cozy','11:00:00','21:30:00','Heritage-home Newari dining in Patan.',800,TRUE),
('The Factory Cafe','Pulchowk, Lalitpur',27.6802,85.3162,'Cafe','Cafe','mid',4.5,167,'lively','08:00:00','22:00:00','Spacious industrial cafe and co-work spot.',750,TRUE),
('Roadhouse Cafe Pulchowk','Pulchowk, Lalitpur',27.6798,85.3178,'Restaurant','Italian','mid',4.4,198,'casual','10:00:00','22:30:00','Patan''s busiest pizza branch.',1100,TRUE),
('Roadhouse Cafe Jhamel','Jhamsikhel, Lalitpur',27.6757,85.3143,'Restaurant','Italian','mid',4.5,254,'casual','10:00:00','22:30:00','Flagship Jhamel pizza and pasta house.',1100,TRUE),
('Tibet Kitchen Thamel','Thamel, Kathmandu',27.7155,85.3114,'Restaurant','Tibetan','mid',4.5,176,'cozy','11:00:00','22:00:00','Refined Tibetan cuisine and butter tea.',900,TRUE),
('Chopstix Thamel','Thamel, Kathmandu',27.7143,85.3118,'Restaurant','Chinese','mid',4.3,143,'casual','11:00:00','22:00:00','Indian-Chinese favourites for groups.',800,TRUE),
('Or-Khid Thai Kitchen','Lazimpat, Kathmandu',27.7222,85.3198,'Restaurant','Thai','mid',4.4,121,'cozy','11:30:00','22:00:00','Aromatic Thai curries and stir-fries.',1100,TRUE),
('Sushi Ko','Durbar Marg, Kathmandu',27.7118,85.3172,'Restaurant','Japanese','expensive',4.5,132,'fine_dining','12:00:00','22:00:00','Fresh sushi and sashimi platters.',1900,TRUE),
('Northfield Cafe','Thamel, Kathmandu',27.7152,85.3128,'Restaurant','Mexican','mid',4.4,176,'garden','07:00:00','22:00:00','Garden cafe known for breakfast and burritos.',1000,TRUE);

INSERT IGNORE INTO restaurants (name,address,latitude,longitude,category,cuisine,price_range,rating,review_count,ambience,opening_time,closing_time,description,avg_cost_per_person,is_active) VALUES
('Cafe Encounter Boudha','Boudha, Kathmandu',27.7210,85.3625,'Cafe','Cafe','mid',4.3,96,'rooftop','07:30:00','20:30:00','Mellow rooftop with stupa views.',600,TRUE),
('Saturday Cafe Boudha','Boudha, Kathmandu',27.7205,85.3632,'Cafe','Cafe','mid',4.5,121,'rooftop','07:30:00','20:00:00','Sunny rooftop brunch near the monasteries.',650,TRUE),
('Ekantakuna Thali House','Ekantakuna, Lalitpur',27.6648,85.3122,'Restaurant','Nepali','budget',4.2,154,'family_friendly','09:00:00','21:00:00','Unlimited daal-bhaat for hungry groups.',450,TRUE),
('Satdobato Momo Center','Satdobato, Lalitpur',27.6582,85.3242,'Restaurant','Nepali','budget',4.3,221,'casual','10:00:00','21:00:00','Popular momo joint on the ring road.',350,TRUE),
('Cafe Hessed','Lagankhel, Lalitpur',27.6668,85.3232,'Cafe','Cafe','mid',4.4,132,'quiet','08:00:00','21:00:00','Calm study cafe with good pastries.',600,TRUE),
('Baber Mahal Cafe','Babar Mahal, Kathmandu',27.6982,85.3268,'Cafe','Cafe','mid',4.4,121,'garden','08:00:00','21:00:00','Courtyard cafe among boutique shops.',700,TRUE),
('Chhetrapati Thakali','Chhetrapati, Kathmandu',27.7112,85.3068,'Restaurant','Thakali','budget',4.3,176,'family_friendly','09:00:00','21:00:00','Classic Thakali set near Thamel''s edge.',500,TRUE),
('Paknajol Rooftop Cafe','Paknajol, Thamel',27.7178,85.3098,'Cafe','Cafe','mid',4.3,109,'rooftop','07:30:00','21:00:00','Quiet rooftop on the north end of Thamel.',600,TRUE),
('Cafe Kalo Pothi','Thamel, Kathmandu',27.7146,85.3124,'Restaurant','Continental','mid',4.3,154,'cozy','08:00:00','22:00:00','Brunch and burgers in central Thamel.',950,TRUE),
('Gokarna Forest Cafe','Gokarna, Kathmandu',27.7468,85.3855,'Cafe','Continental','expensive',4.6,121,'garden','08:00:00','21:00:00','Forest-resort cafe for a quiet escape.',1600,TRUE);


-- =========================================
-- SEED DATA: RESTAURANT OFFERS
-- Linked by restaurant name lookup.
-- INSERT IGNORE prevents duplicates.
-- valid_until is 6 months from a known date;
-- the Python seeder uses today + 180 days.
-- =========================================

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Group brunch discount','20% off on groups of 3+ · Valid today',20,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='cafe de patan' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Free dessert deal','Free dessert with any set meal',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='museum cafe patan' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Newari samay baji combo','Samay baji platter + local drink at a flat rate',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='honacha newari restaurant' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Rooftop happy hour','15% off rooftop platters before 6 PM',15,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='the inn patan' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Heritage thali offer','10% off the Newari heritage thali',10,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='newa chhen restaurant' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Pizza for groups','Buy 2 large pizzas, get 1 garlic bread free',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='fire and ice pizzeria' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Momo combo','Momo + thukpa combo at NPR 499',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='yangling tibetan restaurant' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Veggie mezze deal','15% off the sharing mezze platter',15,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='or2k cushion lounge' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Butter tea on us','Free butter tea with any main course',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='tibet kitchen thamel' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Breakfast special','20% off breakfast sets before 11 AM',20,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='northfield cafe' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Steak night','20% off steaks every weekday evening',20,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='k-too beer & steakhouse' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Coffee combo','Buy 2 coffees, get 1 pastry free',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='java house durbar marg' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Sushi platter offer','15% off the signature sushi platter',15,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='sushi ko' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Pub grub deal','Free fries bucket with any 2 pints',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='the tap house' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Sekuwa group set','10% off sekuwa sets for groups of 4+',10,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='bajeko sekuwa jhamsikhel' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Pizza Tuesday','25% off all pizzas on Tuesdays',25,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='roadhouse cafe jhamel' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Refill hour','Free filter coffee refill before noon',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='karma coffee roasters' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Brunch combo','15% off weekend brunch platters',15,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='the yellow house' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Garden lunch deal','Free dessert with any garden lunch set',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='dhokaima cafe' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Co-work coffee','Buy 1 coffee, get 1 half price all day',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='the factory cafe' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Farm-to-table offer','10% off the farm-to-table tasting plate',10,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='le sherpa restaurant' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Brunch special','Free pastry with any breakfast set',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='cafe cheeno' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Newari evening','15% off Newari platters after 6 PM',15,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='trisara garden lazimpat' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Rooftop veg deal','20% off vegetarian set meals',20,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='stupa view restaurant' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Stupa-view coffee','Buy 2 coffees, get 1 cheesecake free',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='flavors cafe boudha' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Thenthuk combo','Thenthuk + momo combo at NPR 450',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='utse tibetan restaurant' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Study session combo','Buy 2 coffees, get 1 pastry free before 5 PM',0,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='himalayan java coffee' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Cultural dinner offer','10% off the cultural dinner set for groups',10,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='bhojan griha' LIMIT 1;

INSERT IGNORE INTO restaurant_offers (restaurant_id,title,description,discount_percent,valid_from,valid_until,is_active)
SELECT r.id,'Group pizza deal','20% off on orders above NPR 2500',20,CURDATE(),DATE_ADD(CURDATE(),INTERVAL 180 DAY),TRUE
FROM restaurants r WHERE LOWER(TRIM(r.name))='roadhouse cafe' LIMIT 1;
