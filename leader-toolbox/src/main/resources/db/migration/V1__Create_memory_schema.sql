-- Memory System Schema - Initial Migration
-- Description: Creates core tables for memory storage system

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable vector extension for pgvector support (optional, will be used if available)
-- Note: Comment out if pgvector is not available in your PostgreSQL installation
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================
-- Table: memory_documents
-- Purpose: Stores document metadata and source information
-- =============================================
CREATE TABLE memory_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text/plain',
    source_path TEXT,
    source_url TEXT,
    content_hash VARCHAR(64) NOT NULL,
    content_length INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_source CHECK (
        source_path IS NOT NULL OR source_url IS NOT NULL
    ),
    CONSTRAINT chk_content_length CHECK (content_length > 0),
    CONSTRAINT chk_content_hash CHECK (length(content_hash) = 64)
);

-- =============================================
-- Table: memory_chunks
-- Purpose: Stores text chunks with positioning and metadata
-- =============================================
CREATE TABLE memory_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES memory_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    char_start_pos INTEGER NOT NULL,
    char_end_pos INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uk_document_chunk UNIQUE (document_id, chunk_index),
    CONSTRAINT chk_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT chk_token_count CHECK (token_count > 0),
    CONSTRAINT chk_char_positions CHECK (char_end_pos > char_start_pos),
    CONSTRAINT chk_content_not_empty CHECK (length(content) > 0)
);

-- =============================================
-- Table: chunk_embeddings
-- Purpose: Stores vector embeddings for chunks
-- =============================================
CREATE TABLE chunk_embeddings (
    chunk_id UUID PRIMARY KEY REFERENCES memory_chunks(id) ON DELETE CASCADE,
    embedding_vector REAL[] NOT NULL,
    model_name VARCHAR(100) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    vector_dimension INTEGER NOT NULL DEFAULT 384,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_vector_dimension CHECK (
        array_length(embedding_vector, 1) = vector_dimension
    ),
    CONSTRAINT chk_model_name_not_empty CHECK (length(model_name) > 0)
);

-- Add pgvector column if extension is available
-- Note: This will be added conditionally in a later migration if pgvector is detected
-- ALTER TABLE chunk_embeddings ADD COLUMN embedding_vector_pgv vector(384);

-- =============================================
-- Table: memory_sessions
-- Purpose: Tracks user sessions and conversation context
-- =============================================
CREATE TABLE memory_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),
    session_name VARCHAR(200),
    context_data JSONB DEFAULT '{}',
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_session_name_length CHECK (
        session_name IS NULL OR length(session_name) >= 1
    )
);

-- =============================================
-- Table: metadata_tags
-- Purpose: Flexible tagging system for documents and chunks
-- =============================================
CREATE TABLE metadata_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_name VARCHAR(100) NOT NULL,
    tag_value TEXT,
    tag_type VARCHAR(50) NOT NULL DEFAULT 'general',
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('document', 'chunk')),
    target_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uk_tag_target UNIQUE (tag_name, target_type, target_id),
    CONSTRAINT chk_tag_name_not_empty CHECK (length(tag_name) > 0)
);

-- =============================================
-- Table: search_analytics
-- Purpose: Track search queries and performance metrics
-- =============================================
CREATE TABLE search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES memory_sessions(id),
    query_text TEXT NOT NULL,
    query_type VARCHAR(20) NOT NULL CHECK (query_type IN ('semantic', 'keyword', 'hybrid')),
    result_count INTEGER NOT NULL DEFAULT 0,
    execution_time_ms INTEGER NOT NULL,
    top_score REAL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_execution_time CHECK (execution_time_ms >= 0),
    CONSTRAINT chk_result_count CHECK (result_count >= 0)
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Primary performance indexes
CREATE INDEX idx_memory_chunks_document_id ON memory_chunks(document_id);
CREATE INDEX idx_memory_chunks_content_hash ON memory_chunks(content_hash);
CREATE INDEX idx_chunk_embeddings_model ON chunk_embeddings(model_name);
CREATE INDEX idx_memory_documents_created_at ON memory_documents(created_at DESC);
CREATE INDEX idx_memory_documents_content_type ON memory_documents(content_type);
CREATE INDEX idx_memory_sessions_user_id ON memory_sessions(user_id);
CREATE INDEX idx_memory_sessions_last_accessed ON memory_sessions(last_accessed_at DESC);

-- Full-text search indexes
CREATE INDEX idx_memory_documents_title_gin
    ON memory_documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_memory_chunks_content_gin
    ON memory_chunks USING gin(to_tsvector('english', content));

-- JSONB metadata indexes
CREATE INDEX idx_memory_documents_metadata_gin
    ON memory_documents USING gin(metadata);
CREATE INDEX idx_memory_chunks_metadata_gin
    ON memory_chunks USING gin(metadata);
CREATE INDEX idx_memory_sessions_context_gin
    ON memory_sessions USING gin(context_data);

-- Tag system indexes
CREATE INDEX idx_metadata_tags_name ON metadata_tags(tag_name);
CREATE INDEX idx_metadata_tags_type_target ON metadata_tags(target_type, target_id);
CREATE INDEX idx_metadata_tags_name_type ON metadata_tags(tag_name, target_type);

-- Search analytics indexes
CREATE INDEX idx_search_analytics_session ON search_analytics(session_id);
CREATE INDEX idx_search_analytics_query_type ON search_analytics(query_type);
CREATE INDEX idx_search_analytics_created_at ON search_analytics(created_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_documents_not_deleted
    ON memory_documents(created_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_chunks_document_chunk_index
    ON memory_chunks(document_id, chunk_index);

-- =============================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =============================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for memory_documents
CREATE TRIGGER trigger_memory_documents_updated_at
    BEFORE UPDATE ON memory_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update last_accessed_at for sessions
CREATE OR REPLACE FUNCTION update_last_accessed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for memory_sessions
CREATE TRIGGER trigger_memory_sessions_last_accessed
    BEFORE UPDATE ON memory_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_last_accessed_at();

-- =============================================
-- FUNCTIONS FOR VECTOR OPERATIONS
-- =============================================

-- Function to calculate cosine similarity between two float arrays
-- This provides a fallback when pgvector is not available
CREATE OR REPLACE FUNCTION cosine_similarity(vec1 REAL[], vec2 REAL[])
RETURNS REAL AS $$
DECLARE
    dot_product REAL := 0;
    norm1 REAL := 0;
    norm2 REAL := 0;
    i INTEGER;
BEGIN
    -- Ensure vectors are same length
    IF array_length(vec1, 1) != array_length(vec2, 1) THEN
        RAISE EXCEPTION 'Vector dimensions do not match: % vs %',
            array_length(vec1, 1), array_length(vec2, 1);
    END IF;

    -- Calculate dot product and norms
    FOR i IN 1..array_length(vec1, 1) LOOP
        dot_product := dot_product + (vec1[i] * vec2[i]);
        norm1 := norm1 + (vec1[i] * vec1[i]);
        norm2 := norm2 + (vec2[i] * vec2[i]);
    END LOOP;

    -- Avoid division by zero
    IF norm1 = 0 OR norm2 = 0 THEN
        RETURN 0;
    END IF;

    RETURN dot_product / (sqrt(norm1) * sqrt(norm2));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to find top K similar chunks by vector similarity
CREATE OR REPLACE FUNCTION find_similar_chunks(
    query_vector REAL[],
    limit_count INTEGER DEFAULT 10,
    min_similarity REAL DEFAULT 0.3
)
RETURNS TABLE(
    chunk_id UUID,
    similarity_score REAL,
    content TEXT,
    document_title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        mc.id,
        cosine_similarity(ce.embedding_vector, query_vector) as similarity,
        mc.content,
        md.title
    FROM memory_chunks mc
    JOIN chunk_embeddings ce ON mc.id = ce.chunk_id
    JOIN memory_documents md ON mc.document_id = md.id
    WHERE md.deleted_at IS NULL
      AND cosine_similarity(ce.embedding_vector, query_vector) >= min_similarity
    ORDER BY similarity DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- View for document summaries with chunk counts
CREATE VIEW document_summaries AS
SELECT
    md.id,
    md.title,
    md.content_type,
    md.source_path,
    md.source_url,
    md.content_length,
    md.metadata,
    md.created_at,
    md.updated_at,
    COUNT(mc.id) as chunk_count,
    COALESCE(SUM(mc.token_count), 0) as total_tokens
FROM memory_documents md
LEFT JOIN memory_chunks mc ON md.id = mc.document_id
WHERE md.deleted_at IS NULL
GROUP BY md.id, md.title, md.content_type, md.source_path,
         md.source_url, md.content_length, md.metadata,
         md.created_at, md.updated_at;

-- View for chunk details with document context
CREATE VIEW chunk_details AS
SELECT
    mc.id as chunk_id,
    mc.document_id,
    mc.chunk_index,
    mc.content,
    mc.token_count,
    mc.char_start_pos,
    mc.char_end_pos,
    mc.metadata as chunk_metadata,
    mc.created_at as chunk_created_at,
    md.title as document_title,
    md.content_type,
    md.source_path,
    md.source_url,
    md.metadata as document_metadata,
    ce.model_name,
    ce.vector_dimension,
    ce.created_at as embedding_created_at
FROM memory_chunks mc
JOIN memory_documents md ON mc.document_id = md.id
LEFT JOIN chunk_embeddings ce ON mc.id = ce.chunk_id
WHERE md.deleted_at IS NULL;

-- =============================================
-- COMMENTS AND DOCUMENTATION
-- =============================================

-- Add comments to tables for documentation
COMMENT ON TABLE memory_documents IS 'Stores document metadata and source information';
COMMENT ON TABLE memory_chunks IS 'Text chunks extracted from documents with position tracking';
COMMENT ON TABLE chunk_embeddings IS 'Vector embeddings for semantic search capabilities';
COMMENT ON TABLE memory_sessions IS 'User session tracking for context management';
COMMENT ON TABLE metadata_tags IS 'Flexible tagging system for content organization';
COMMENT ON TABLE search_analytics IS 'Search query performance and usage tracking';

-- Add comments to key columns
COMMENT ON COLUMN memory_documents.content_hash IS 'SHA-256 hash of document content for deduplication';
COMMENT ON COLUMN memory_chunks.content_hash IS 'SHA-256 hash of chunk content for change detection';
COMMENT ON COLUMN chunk_embeddings.embedding_vector IS 'Dense vector representation for semantic search';
COMMENT ON COLUMN memory_sessions.context_data IS 'JSON context data for conversation state';

-- =============================================
-- SAMPLE DATA FOR TESTING (Optional)
-- =============================================

-- Insert sample document for testing (uncomment if needed)
/*
INSERT INTO memory_documents (id, title, content_type, source_path, content_hash, content_length, metadata)
VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'Sample Memory Document',
    'text/plain',
    '/test/sample.txt',
    '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d',
    1000,
    '{"category": "test", "priority": "high"}'::jsonb
);

INSERT INTO memory_chunks (id, document_id, chunk_index, content, token_count, char_start_pos, char_end_pos, content_hash)
VALUES (
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'a0000000-0000-0000-0000-000000000001'::uuid,
    0,
    'This is a sample chunk of text for testing the memory system. It contains enough content to be meaningful for search operations.',
    25,
    0,
    139,
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
);
*/