-- SQL Script to set up tables for Expert Flag Labeler in Supabase
-- Run this in the Supabase SQL Editor

-- Create table for image metadata
CREATE TABLE IF NOT EXISTS image_metadata (
  id SERIAL PRIMARY KEY,
  town TEXT NOT NULL,
  filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  composite_path TEXT,
  has_composite BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Compound unique constraint
  UNIQUE(town, filename)
);

-- Create classifications table
CREATE TABLE IF NOT EXISTS classifications (
  id SERIAL PRIMARY KEY,
  image_path TEXT NOT NULL,
  town TEXT NOT NULL,
  primary_category TEXT NOT NULL,
  specific_type TEXT,
  display_context TEXT,
  confidence INTEGER,
  user_name TEXT,
  notes TEXT,
  needs_review BOOLEAN DEFAULT FALSE,
  review_reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_image_metadata_town ON image_metadata(town);
CREATE INDEX IF NOT EXISTS idx_image_metadata_filename ON image_metadata(filename);
CREATE INDEX IF NOT EXISTS idx_classifications_image_path ON classifications(image_path);
CREATE INDEX IF NOT EXISTS idx_classifications_town ON classifications(town);
CREATE INDEX IF NOT EXISTS idx_classifications_created_at ON classifications(created_at);

-- Set up Row Level Security
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;

-- Create policies for public access to images metadata
DROP POLICY IF EXISTS "Anyone can read image metadata" ON image_metadata;
CREATE POLICY "Anyone can read image metadata"
ON image_metadata
FOR SELECT
USING (true);

-- Create policies for classifications
DROP POLICY IF EXISTS "Anyone can read classifications" ON classifications;
CREATE POLICY "Anyone can read classifications"
ON classifications
FOR SELECT
USING (true);

DROP POLICY IF EXISTS "Authenticated users can insert classifications" ON classifications;
CREATE POLICY "Authenticated users can insert classifications"
ON classifications
FOR INSERT
USING (auth.role() = 'authenticated');

-- Create a stored procedure to create image_metadata table if it doesn't exist
CREATE OR REPLACE FUNCTION create_image_metadata_if_not_exists()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  IF NOT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'image_metadata'
  ) THEN
    CREATE TABLE image_metadata (
      id SERIAL PRIMARY KEY,
      town TEXT NOT NULL,
      filename TEXT NOT NULL,
      storage_path TEXT NOT NULL,
      composite_path TEXT,
      has_composite BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      UNIQUE(town, filename)
    );
    
    CREATE INDEX idx_image_metadata_town ON image_metadata(town);
    CREATE INDEX idx_image_metadata_filename ON image_metadata(filename);
    
    ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY "Anyone can read image metadata"
      ON image_metadata
      FOR SELECT
      USING (true);
  END IF;
END;
$$;

-- Create a stored procedure to generate a summary of classifications
CREATE OR REPLACE FUNCTION summarize_classifications()
RETURNS TABLE (
  category TEXT,
  count BIGINT,
  percentage NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH total AS (SELECT COUNT(*) as total_count FROM classifications)
  SELECT 
    primary_category, 
    COUNT(*) as count,
    ROUND((COUNT(*) * 100.0 / total.total_count), 2) as percentage
  FROM 
    classifications, total
  GROUP BY 
    primary_category, total.total_count
  ORDER BY 
    count DESC;
END;
$$;