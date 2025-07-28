-- Add Unique Constraint to Prevent Duplicate Classifications
-- ⚠️  WARNING: This script DELETES existing duplicate classifications!
-- ⚠️  Only run this if you're okay with removing older duplicates
-- ⚠️  Use scripts/add-constraint-safe.sql if you want no data deletion

-- STEP 1: Clean up existing duplicates (DELETES DATA!)
-- This will keep only the most recent classification for each user-image pair
WITH duplicates AS (
  SELECT 
    expert_id,
    image_id,
    MAX(timestamp) as latest_timestamp
  FROM classifications
  GROUP BY expert_id, image_id
  HAVING COUNT(*) > 1
)
DELETE FROM classifications c
WHERE EXISTS (
  SELECT 1 FROM duplicates d 
  WHERE d.expert_id = c.expert_id 
  AND d.image_id = c.image_id 
  AND c.timestamp < d.latest_timestamp
);

-- STEP 2: Add unique constraint to prevent future duplicates
ALTER TABLE classifications 
ADD CONSTRAINT unique_user_image_classification 
UNIQUE (expert_id, image_id);

-- Create an index for faster lookups
CREATE INDEX IF NOT EXISTS idx_classifications_expert_image 
ON classifications(expert_id, image_id);

-- Optional: Add a function to check if user has already classified an image
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