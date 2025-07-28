-- Safe Constraint Addition (No Data Deletion)
-- Run this ONLY if check-for-duplicates.sql shows "NO duplicates"

-- Add unique constraint to prevent future duplicates
ALTER TABLE classifications 
ADD CONSTRAINT unique_user_image_classification 
UNIQUE (expert_id, image_id);

-- Create an index for faster lookups
CREATE INDEX IF NOT EXISTS idx_classifications_expert_image 
ON classifications(expert_id, image_id);

-- Add a function to check if user has already classified an image
CREATE OR REPLACE FUNCTION user_has_classified_image(p_expert_id TEXT, p_image_id TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM classifications 
    WHERE expert_id = p_expert_id AND image_id = p_image_id
  );
END;
$$; 