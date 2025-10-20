-- Google Cloud SQL Database Schema for PDF to CSV Pipeline
-- This schema supports collections, batches, files, and records management

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Collections table - represents client datasets
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'processing')),
    notes TEXT,
    batch_id VARCHAR(100),
    total_records INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Batches table - represents processing groups of PDFs
CREATE TABLE batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    batch_name VARCHAR(255) NOT NULL,
    group_size INTEGER DEFAULT 25,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    total_records INTEGER DEFAULT 0,
    filtered_records INTEGER DEFAULT 0,
    duplicates_found INTEGER DEFAULT 0,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Files table - represents individual PDF files
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed', 'ignored')),
    pages INTEGER,
    document_ai_operation_id VARCHAR(255),
    raw_json_path TEXT,
    processing_time_seconds DECIMAL(10,2),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Records table - represents extracted contact records
CREATE TABLE records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    mobile VARCHAR(20),
    landline VARCHAR(20),
    address TEXT,
    email VARCHAR(255),
    date_of_birth VARCHAR(50),
    last_seen_date VARCHAR(50),
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_group_id UUID,
    is_valid BOOLEAN DEFAULT TRUE,
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Duplicate groups table - for tracking duplicate records
CREATE TABLE duplicate_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    mobile_number VARCHAR(20) NOT NULL,
    record_count INTEGER DEFAULT 1,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_action VARCHAR(50) CHECK (resolution_action IN ('keep_first', 'keep_most_complete', 'manual_merge', 'ignore')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Processing logs table - for audit trail
CREATE TABLE processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG')),
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Export history table - for tracking exports
CREATE TABLE export_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL CHECK (export_type IN ('zip_all', 'filtered_csv', 'raw_csv', 'excel')),
    file_path TEXT,
    file_size BIGINT,
    record_count INTEGER,
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_collections_status ON collections(status);
CREATE INDEX idx_collections_client ON collections(client_name);
CREATE INDEX idx_collections_created_date ON collections(created_date);

CREATE INDEX idx_batches_collection_id ON batches(collection_id);
CREATE INDEX idx_batches_status ON batches(status);

CREATE INDEX idx_files_batch_id ON files(batch_id);
CREATE INDEX idx_files_status ON files(status);

CREATE INDEX idx_records_batch_id ON records(batch_id);
CREATE INDEX idx_records_file_id ON records(file_id);
CREATE INDEX idx_records_mobile ON records(mobile);
CREATE INDEX idx_records_is_duplicate ON records(is_duplicate);
CREATE INDEX idx_records_is_valid ON records(is_valid);

CREATE INDEX idx_duplicate_groups_batch_id ON duplicate_groups(batch_id);
CREATE INDEX idx_duplicate_groups_mobile ON duplicate_groups(mobile_number);

CREATE INDEX idx_processing_logs_batch_id ON processing_logs(batch_id);
CREATE INDEX idx_processing_logs_created_at ON processing_logs(created_at);

CREATE INDEX idx_export_history_collection_id ON export_history(collection_id);
CREATE INDEX idx_export_history_batch_id ON export_history(batch_id);

-- Triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_batches_updated_at BEFORE UPDATE ON batches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_records_updated_at BEFORE UPDATE ON records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_duplicate_groups_updated_at BEFORE UPDATE ON duplicate_groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update collection total_records count
CREATE OR REPLACE FUNCTION update_collection_record_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE collections 
        SET total_records = (
            SELECT COUNT(*) 
            FROM records r 
            JOIN batches b ON r.batch_id = b.id 
            WHERE b.collection_id = NEW.batch_id
        )
        WHERE id = (SELECT collection_id FROM batches WHERE id = NEW.batch_id);
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE collections 
        SET total_records = (
            SELECT COUNT(*) 
            FROM records r 
            JOIN batches b ON r.batch_id = b.id 
            WHERE b.collection_id = (SELECT collection_id FROM batches WHERE id = OLD.batch_id)
        )
        WHERE id = (SELECT collection_id FROM batches WHERE id = OLD.batch_id);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

CREATE TRIGGER update_collection_record_count_trigger
    AFTER INSERT OR UPDATE OR DELETE ON records
    FOR EACH ROW EXECUTE FUNCTION update_collection_record_count();

-- Function to detect and flag duplicates
CREATE OR REPLACE FUNCTION detect_duplicates_in_batch(batch_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    duplicate_count INTEGER := 0;
    rec RECORD;
BEGIN
    -- Clear existing duplicate flags for this batch
    UPDATE records SET is_duplicate = FALSE, duplicate_group_id = NULL WHERE batch_id = batch_uuid;
    
    -- Find duplicates by mobile number
    FOR rec IN 
        SELECT mobile, COUNT(*) as count, array_agg(id) as record_ids
        FROM records 
        WHERE batch_id = batch_uuid AND mobile IS NOT NULL AND mobile != ''
        GROUP BY mobile 
        HAVING COUNT(*) > 1
    LOOP
        -- Create duplicate group
        INSERT INTO duplicate_groups (batch_id, mobile_number, record_count)
        VALUES (batch_uuid, rec.mobile, rec.count);
        
        -- Get the duplicate group ID
        DECLARE
            group_id UUID;
        BEGIN
            SELECT id INTO group_id FROM duplicate_groups 
            WHERE batch_id = batch_uuid AND mobile_number = rec.mobile 
            ORDER BY created_at DESC LIMIT 1;
            
            -- Flag all records in this group as duplicates
            UPDATE records 
            SET is_duplicate = TRUE, duplicate_group_id = group_id
            WHERE id = ANY(rec.record_ids);
            
            duplicate_count := duplicate_count + rec.count;
        END;
    END LOOP;
    
    -- Update batch duplicate count
    UPDATE batches 
    SET duplicates_found = duplicate_count 
    WHERE id = batch_uuid;
    
    RETURN duplicate_count;
END;
$$ language 'plpgsql';

-- Sample data for testing
INSERT INTO collections (collection_name, client_name, notes, batch_id) VALUES
('Weekly Data - Week 1', 'ABC Company', 'Initial data collection for Q1 campaign', 'BATCH-001'),
('Weekly Data - Week 2', 'ABC Company', 'Follow-up data for Q1 campaign', 'BATCH-002'),
('Test Collection', 'XYZ Corp', 'Testing the new system', 'BATCH-003');
