-- Check for Duplicate Classifications WITHIN Same User
-- Run this in Supabase SQL Editor to see if you have duplicates
-- Note: Multiple users classifying same image is EXPECTED and desired

-- Count total classifications
SELECT 'Total Classifications' as type, COUNT(*) as count FROM classifications;

-- Count unique user-image pairs
SELECT 'Unique User-Image Pairs' as type, COUNT(*) as count 
FROM (
  SELECT DISTINCT expert_id, image_id FROM classifications
) as unique_pairs;

-- Find actual duplicates (if any)
SELECT 
  expert_id,
  image_id,
  COUNT(*) as duplicate_count,
  MIN(timestamp) as first_classification,
  MAX(timestamp) as latest_classification
FROM classifications
GROUP BY expert_id, image_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, expert_id, image_id;

-- Summary: Show if you have duplicates
SELECT 
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM classifications 
      GROUP BY expert_id, image_id 
      HAVING COUNT(*) > 1
    ) 
    THEN 'YES - You have duplicate classifications (same user, same image)' 
    ELSE 'NO - No duplicates found, safe to add constraint'
  END as has_duplicates; 