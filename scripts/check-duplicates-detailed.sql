-- Check for duplicate classifications WITHIN the same user (this is the problem)
SELECT 
    expert_id,
    COUNT(*) as total_classifications,
    COUNT(DISTINCT image_id) as unique_images,
    COUNT(*) - COUNT(DISTINCT image_id) as duplicate_count
FROM classifications 
GROUP BY expert_id
HAVING COUNT(*) > COUNT(DISTINCT image_id)
ORDER BY duplicate_count DESC;

-- Show actual duplicate entries (same user classifying same image multiple times)
SELECT 
    expert_id,
    image_id,
    COUNT(*) as times_classified,
    STRING_AGG(DISTINCT primary_category, ', ') as different_classifications,
    STRING_AGG(DISTINCT timestamp::text, ', ' ORDER BY timestamp::text) as timestamps
FROM classifications 
GROUP BY expert_id, image_id
HAVING COUNT(*) > 1
ORDER BY expert_id, times_classified DESC; 