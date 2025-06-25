-- Safe SQL Script to set up tables for Expert Flag Labeler in Supabase
-- Run this in the Supabase SQL Editor

-- Create table for image metadata if it doesn't exist
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

-- Create classifications table if it doesn't exist
CREATE TABLE IF NOT EXISTS classifications (
  id SERIAL PRIMARY KEY,
  image_path TEXT NOT NULL,  -- This is the path/ID of the image being classified
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
CREATE INDEX IF NOT EXISTS idx_classifications_town ON classifications(town);
CREATE INDEX IF NOT EXISTS idx_classifications_created_at ON classifications(created_at);

-- Create index for the image_path column in classifications table
CREATE INDEX IF NOT EXISTS idx_classifications_image_path ON classifications(image_path);

-- Set up Row Level Security
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;

-- Create policies one by one to avoid errors
-- Policy for image_metadata
CREATE POLICY IF NOT EXISTS "Anyone can read image metadata"
ON image_metadata
FOR SELECT
USING (true);

-- Policies for classifications
CREATE POLICY IF NOT EXISTS "Anyone can read classifications"
ON classifications
FOR SELECT
USING (true);

CREATE POLICY IF NOT EXISTS "Anyone can insert classifications"
ON classifications
FOR INSERT
USING (true);

-- Create a stored procedure for generating classification summaries
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