-- ==========================================
-- FinMate Database Initialization Script
-- ==========================================
-- WARNING: This script drops and recreates all tables.
-- For existing databases, run only the CREATE TABLE block
-- for transactions (section below).
-- ==========================================

DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ==========================================
-- Users Table
-- ==========================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(255) NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- ==========================================
-- Transactions Table
-- ==========================================

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    date DATE NOT NULL,

    merchant VARCHAR(255) NOT NULL,

    description TEXT,

    amount FLOAT NOT NULL,

    transaction_type VARCHAR(10) NOT NULL DEFAULT 'debit',

    category VARCHAR(100) NOT NULL DEFAULT 'Other',

    source_file VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_category ON transactions(category);

-- ==========================================
-- Verification
-- ==========================================

SELECT 'FinMate database initialized successfully' AS message;
