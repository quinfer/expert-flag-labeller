-- Simple Statistical Summary for Flag Classifications
-- This provides key statistics in a more readable format

-- 1. OVERALL SUMMARY
SELECT 
  'CLASSIFICATION SUMMARY' as section,
  COUNT(*) as total_classifications,
  COUNT(DISTINCT image_id) as unique_images,
  COUNT(DISTINCT expert_id) as active_experts,
  COUNT(DISTINCT town) as towns_covered,
  COUNT(DISTINCT primary_category) as categories_used,
  ROUND(AVG(confidence), 2) as avg_confidence,
  COUNT(*) FILTER (WHERE needs_review = true) as flagged_for_review,
  ROUND(COUNT(*) FILTER (WHERE needs_review = true) * 100.0 / COUNT(*), 1) as review_rate_percent
FROM classifications;

-- 2. TOP FLAG TYPES
SELECT 
  'TOP FLAG TYPES' as section,
  specific_flag as flag_type,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
  ROUND(AVG(confidence), 2) as avg_confidence
FROM classifications 
WHERE specific_flag IS NOT NULL
GROUP BY specific_flag 
ORDER BY count DESC 
LIMIT 10;

-- 3. PRIMARY CATEGORIES
SELECT 
  'PRIMARY CATEGORIES' as section,
  primary_category,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
  ROUND(AVG(confidence), 2) as avg_confidence,
  COUNT(DISTINCT expert_id) as experts_involved
FROM classifications 
GROUP BY primary_category 
ORDER BY count DESC;

-- 4. DISPLAY CONTEXTS
SELECT 
  'DISPLAY CONTEXTS' as section,
  COALESCE(display_context, 'Not Specified') as context,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM classifications 
GROUP BY display_context 
ORDER BY count DESC;

-- 5. CONFIDENCE DISTRIBUTION
SELECT 
  'CONFIDENCE SCORES' as section,
  confidence as score,
  COUNT(*) as frequency,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
  SUM(COUNT(*)) OVER (ORDER BY confidence) as cumulative_count
FROM classifications 
WHERE confidence IS NOT NULL
GROUP BY confidence 
ORDER BY confidence;

-- 6. TOP TOWNS BY ACTIVITY
SELECT 
  'TOP TOWNS' as section,
  town,
  COUNT(*) as classifications,
  COUNT(DISTINCT image_id) as unique_images,
  COUNT(DISTINCT expert_id) as experts,
  ROUND(AVG(confidence), 2) as avg_confidence
FROM classifications 
GROUP BY town 
ORDER BY classifications DESC 
LIMIT 10;

-- 7. EXPERT ACTIVITY
SELECT 
  'EXPERT ACTIVITY' as section,
  expert_id,
  COUNT(*) as total_classifications,
  COUNT(DISTINCT image_id) as unique_images,
  COUNT(DISTINCT town) as towns_worked,
  ROUND(AVG(confidence), 2) as avg_confidence,
  MAX(timestamp)::date as last_active
FROM classifications 
WHERE expert_id IS NOT NULL
GROUP BY expert_id 
ORDER BY total_classifications DESC;

-- 8. RECENT ACTIVITY (Last 7 days)
SELECT 
  'RECENT ACTIVITY' as section,
  DATE(timestamp) as date,
  COUNT(*) as classifications,
  COUNT(DISTINCT expert_id) as active_experts,
  ROUND(AVG(confidence), 2) as avg_confidence
FROM classifications 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp) 
ORDER BY date DESC;

SELECT 'ANALYSIS COMPLETED' as status, CURRENT_TIMESTAMP as completed_at; 