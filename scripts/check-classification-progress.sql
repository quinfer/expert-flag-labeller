-- Classification Progress Report
-- Run these queries in Supabase SQL Editor to check classification status

-- 1. OVERALL CLASSIFICATION SUMMARY
SELECT 
  'Total Classifications' as metric,
  COUNT(*) as count
FROM classifications

UNION ALL

SELECT 
  'Unique Images Classified' as metric,
  COUNT(DISTINCT image_id) as count
FROM classifications

UNION ALL

SELECT 
  'Images Flagged for Review' as metric,
  COUNT(*) as count
FROM classifications 
WHERE needs_review = true

UNION ALL

SELECT 
  'Average Confidence' as metric,
  ROUND(AVG(confidence), 2) as count
FROM classifications 
WHERE confidence IS NOT NULL;

-- 2. CLASSIFICATION BREAKDOWN BY PRIMARY CATEGORY
SELECT 
  primary_category,
  COUNT(*) as total_classifications,
  COUNT(DISTINCT image_id) as unique_images,
  ROUND(AVG(confidence), 2) as avg_confidence,
  ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM classifications)), 2) as percentage
FROM classifications 
GROUP BY primary_category 
ORDER BY total_classifications DESC;

-- 3. CLASSIFICATION PROGRESS BY TOWN
SELECT 
  town,
  COUNT(*) as classifications,
  COUNT(DISTINCT image_id) as unique_images,
  COUNT(DISTINCT expert_id) as active_users,
  ROUND(AVG(confidence), 2) as avg_confidence
FROM classifications 
GROUP BY town 
ORDER BY classifications DESC;

-- 4. USER ACTIVITY SUMMARY
SELECT 
  expert_id,
  COUNT(*) as total_classifications,
  COUNT(DISTINCT image_id) as unique_images,
  COUNT(DISTINCT town) as towns_worked,
  ROUND(AVG(confidence), 2) as avg_confidence,
  MIN(timestamp) as first_classification,
  MAX(timestamp) as last_classification
FROM classifications 
WHERE expert_id IS NOT NULL
GROUP BY expert_id 
ORDER BY total_classifications DESC;

-- 5. RECENT ACTIVITY (Last 7 days)
SELECT 
  DATE(timestamp) as classification_date,
  COUNT(*) as classifications_per_day,
  COUNT(DISTINCT expert_id) as active_users,
  COUNT(DISTINCT image_id) as unique_images
FROM classifications 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp) 
ORDER BY classification_date DESC;

-- 6. IMAGES FLAGGED FOR REVIEW
SELECT 
  review_reason,
  COUNT(*) as count,
  ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM classifications WHERE needs_review = true)), 2) as percentage
FROM classifications 
WHERE needs_review = true AND review_reason IS NOT NULL
GROUP BY review_reason 
ORDER BY count DESC;

-- 7. HOURLY ACTIVITY PATTERN (to see when people are most active)
SELECT 
  EXTRACT(hour FROM timestamp) as hour_of_day,
  COUNT(*) as classifications,
  COUNT(DISTINCT expert_id) as active_users
FROM classifications 
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY EXTRACT(hour FROM timestamp) 
ORDER BY hour_of_day;

-- 8. CONFIDENCE DISTRIBUTION
SELECT 
  confidence,
  COUNT(*) as count,
  ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM classifications WHERE confidence IS NOT NULL)), 2) as percentage
FROM classifications 
WHERE confidence IS NOT NULL
GROUP BY confidence 
ORDER BY confidence;

-- 9. PROGRESS COMPARISON (if image_metadata table has data)
SELECT 
  'Total Available Images' as metric,
  COUNT(*) as count
FROM image_metadata

UNION ALL

SELECT 
  'Images Classified' as metric,
  COUNT(DISTINCT c.image_id) as count
FROM classifications c

UNION ALL

SELECT 
  'Classification Progress %' as metric,
  ROUND((COUNT(DISTINCT c.image_id) * 100.0 / (SELECT COUNT(*) FROM image_metadata)), 2) as count
FROM classifications c;

-- 10. TOP PERFORMERS (Users with most classifications in last 30 days)
SELECT 
  expert_id,
  COUNT(*) as recent_classifications,
  COUNT(DISTINCT image_id) as unique_images,
  ROUND(AVG(confidence), 2) as avg_confidence,
  MAX(timestamp) as last_active
FROM classifications 
WHERE timestamp >= NOW() - INTERVAL '30 days' 
  AND expert_id IS NOT NULL
GROUP BY expert_id 
ORDER BY recent_classifications DESC 
LIMIT 10; 