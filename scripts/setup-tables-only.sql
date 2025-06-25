-- Simplified SQL Script - Tables Only
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
CREATE INDEX IF NOT EXISTS idx_classifications_image_path ON classifications(image_path);