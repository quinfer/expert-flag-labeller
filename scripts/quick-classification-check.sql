-- Quick Classification Progress Check
-- Run this in Supabase SQL Editor for a fast overview

SELECT 
  'Total Classifications' as metric,
  COUNT(*) as value,
  '' as details
FROM classifications

UNION ALL

SELECT 
  'Unique Images Classified' as metric,
  COUNT(DISTINCT image_id) as value,
  '' as details
FROM classifications

UNION ALL

SELECT 
  'Active Users' as metric,
  COUNT(DISTINCT expert_id) as value,
  '' as details
FROM classifications 
WHERE expert_id IS NOT NULL

UNION ALL

SELECT 
  'Images Flagged for Review' as metric,
  COUNT(*) as value,
  CONCAT(ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM classifications)), 1), '%') as details
FROM classifications 
WHERE needs_review = true

UNION ALL

SELECT 
  'Average Confidence Score' as metric,
  ROUND(AVG(confidence), 1) as value,
  '/5.0' as details
FROM classifications 
WHERE confidence IS NOT NULL

UNION ALL

SELECT 
  'Classifications Today' as metric,
  COUNT(*) as value,
  '' as details
FROM classifications 
WHERE DATE(timestamp) = CURRENT_DATE

UNION ALL

SELECT 
  'Classifications This Week' as metric,
  COUNT(*) as value,
  '' as details
FROM classifications 
WHERE timestamp >= DATE_TRUNC('week', CURRENT_DATE)

ORDER BY 
  CASE metric
    WHEN 'Total Classifications' THEN 1
    WHEN 'Unique Images Classified' THEN 2
    WHEN 'Active Users' THEN 3
    WHEN 'Images Flagged for Review' THEN 4
    WHEN 'Average Confidence Score' THEN 5
    WHEN 'Classifications Today' THEN 6
    WHEN 'Classifications This Week' THEN 7
  END; 