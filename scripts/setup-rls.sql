-- RLS Policies - Run after creating tables
-- Run this in the Supabase SQL Editor

-- Set up Row Level Security
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;

-- Create policy for image_metadata
CREATE POLICY "Anyone can read image metadata"
ON image_metadata
FOR SELECT
USING (true);

-- Create policies for classifications
CREATE POLICY "Anyone can read classifications"
ON classifications
FOR SELECT
USING (true);

CREATE POLICY "Anyone can insert classifications"
ON classifications
FOR INSERT
USING (true);