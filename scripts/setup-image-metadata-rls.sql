-- RLS Policies for Image Metadata Table
-- Run this in the Supabase SQL Editor

-- Set up Row Level Security
ALTER TABLE image_metadata ENABLE ROW LEVEL SECURITY;

-- Create policy for image_metadata
CREATE POLICY "Anyone can read image metadata"
ON image_metadata
FOR SELECT
USING (true);