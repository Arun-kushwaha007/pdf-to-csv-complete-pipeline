-- Database schema for PDF to CSV Pipeline
-- This creates tables for storing raw and filtered records

-- Create database if it doesn't exist (run this manually in Cloud SQL)
-- CREATE DATABASE pdf2csv_db;

-- Use the database
-- \c pdf2csv_db;

-- Create raw_records table
CREATE TABLE IF NOT EXISTS raw_records (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    mobile VARCHAR(20),
    landline VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    date_of_birth VARCHAR(50),
    last_seen VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create filtered_records table
CREATE TABLE IF NOT EXISTS filtered_records (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) NOT NULL,
    landline VARCHAR(20),
    email VARCHAR(255),
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mobile) -- Prevent duplicate mobile numbers
);

-- Create processing_sessions table to track batches
CREATE TABLE IF NOT EXISTS processing_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255) NOT NULL,
    total_files INTEGER DEFAULT 0,
    raw_records_count INTEGER DEFAULT 0,
    filtered_records_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'completed'
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_raw_records_file_name ON raw_records(file_name);
CREATE INDEX IF NOT EXISTS idx_raw_records_mobile ON raw_records(mobile);
CREATE INDEX IF NOT EXISTS idx_raw_records_created_at ON raw_records(created_at);

CREATE INDEX IF NOT EXISTS idx_filtered_records_file_name ON filtered_records(file_name);
CREATE INDEX IF NOT EXISTS idx_filtered_records_mobile ON filtered_records(mobile);
CREATE INDEX IF NOT EXISTS idx_filtered_records_created_at ON filtered_records(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_raw_records_updated_at 
    BEFORE UPDATE ON raw_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_filtered_records_updated_at 
    BEFORE UPDATE ON filtered_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
