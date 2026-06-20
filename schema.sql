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

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    ON DELETE CASCADE
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
    status   ENUM('open', 'closed') NOT NULL DEFAULT 'open',

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
