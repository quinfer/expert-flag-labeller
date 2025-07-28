-- Clean up test duplicates - keep only the most recent classification per user-image pair
-- This script removes duplicate classifications, keeping only the latest one based on timestamp

-- First, let's see what we're about to clean up
SELECT 
    'BEFORE CLEANUP' as status,
    COUNT(*) as total_classifications,
    COUNT(DISTINCT CONCAT(expert_id, '-', image_id)) as unique_user_image_pairs,
    COUNT(*) - COUNT(DISTINCT CONCAT(expert_id, '-', image_id)) as duplicates_to_remove
FROM classifications;

-- Show the duplicates that will be removed (for verification)
SELECT 
    expert_id,
    image_id,
    COUNT(*) as duplicate_count,
    MIN(timestamp) as oldest_classification,
    MAX(timestamp) as newest_classification_to_keep
FROM classifications
GROUP BY expert_id, image_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- *** ACTUAL CLEANUP - UNCOMMENT TO RUN ***
DELETE FROM classifications 
WHERE id IN (
    SELECT id FROM (
        SELECT 
            id,
            ROW_NUMBER() OVER (
                PARTITION BY expert_id, image_id 
                ORDER BY timestamp DESC
            ) as rn
        FROM classifications
    ) ranked
    WHERE rn > 1
);

-- After cleanup verification (uncomment after running the DELETE above)
SELECT 
    'AFTER CLEANUP' as status,
    COUNT(*) as total_classifications,
    COUNT(DISTINCT CONCAT(expert_id, '-', image_id)) as unique_user_image_pairs,
    COUNT(*) - COUNT(DISTINCT CONCAT(expert_id, '-', image_id)) as should_be_zero
FROM classifications; 