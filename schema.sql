-- =========================================
-- CREATE DATABASE
-- =========================================

CREATE DATABASE IF NOT EXISTS bhetamla_db;
USE bhetamla_db;


-- =========================================
-- EMAIL VERIFICATION
-- =========================================
-- 1. Turn off safe updates
-- SET SQL_SAFE_UPDATES = 0;
-- 2. Run your update query
-- UPDATE users SET is_verified = 1;
-- 3. Turn safe updates back on (recommended for safety)
-- SET SQL_SAFE_UPDATES = 1;
-- 4. Check your results
-- SELECT id, email, is_verified FROM users;
-- to unverify
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



