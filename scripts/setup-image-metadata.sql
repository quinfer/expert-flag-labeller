-- Setup Image Metadata Table Only
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

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_image_metadata_town ON image_metadata(town);
CREATE INDEX IF NOT EXISTS idx_image_metadata_filename ON image_metadata(filename);