-- Consolidated Statistics - Single Result Table
-- This combines all statistics into one visible result

WITH base_stats AS (
  SELECT 
    COUNT(*) as total_classifications,
    COUNT(DISTINCT image_id) as unique_images,
    COUNT(DISTINCT expert_id) as active_experts,
    COUNT(DISTINCT town) as towns_covered,
    COUNT(DISTINCT primary_category) as categories_used,
    AVG(confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE needs_review = true) as flagged_for_review
  FROM classifications
),
all_stats AS (
-- OVERALL SUMMARY
SELECT 
  'OVERALL SUMMARY' as category,
  'Total Classifications' as metric,
  total_classifications::text as value,
  '' as percentage
FROM base_stats

UNION ALL

SELECT 
  'OVERALL SUMMARY',
  'Unique Images',
  unique_images::text,
  ROUND((unique_images::numeric / total_classifications * 100), 1)::text || '%'
FROM base_stats

UNION ALL

SELECT 
  'OVERALL SUMMARY',
  'Active Experts',
  active_experts::text,
  ''
FROM base_stats

UNION ALL

SELECT 
  'OVERALL SUMMARY',
  'Towns Covered',
  towns_covered::text,
  ''
FROM base_stats

UNION ALL

SELECT 
  'OVERALL SUMMARY',
  'Average Confidence',
  ROUND(avg_confidence::numeric, 2)::text,
  ''
FROM base_stats

UNION ALL

SELECT 
  'OVERALL SUMMARY',
  'Flagged for Review',
  flagged_for_review::text,
  ROUND((flagged_for_review::numeric / total_classifications * 100), 1)::text || '%'
FROM base_stats

UNION ALL

-- TOP FLAG TYPES
SELECT 
  'TOP FLAG TYPES' as category,
  specific_flag as metric,
  COUNT(*)::text as value,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)::text || '%' as percentage
FROM classifications 
WHERE specific_flag IS NOT NULL
GROUP BY specific_flag

UNION ALL

-- PRIMARY CATEGORIES
SELECT 
  'PRIMARY CATEGORIES' as category,
  primary_category as metric,
  COUNT(*)::text as value,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)::text || '%' as percentage
FROM classifications 
GROUP BY primary_category

UNION ALL

-- DISPLAY CONTEXTS
SELECT 
  'DISPLAY CONTEXTS' as category,
  COALESCE(display_context, 'Not Specified') as metric,
  COUNT(*)::text as value,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)::text || '%' as percentage
FROM classifications 
GROUP BY display_context

UNION ALL

-- CONFIDENCE SCORES
SELECT 
  'CONFIDENCE SCORES' as category,
  'Score ' || confidence::text as metric,
  COUNT(*)::text as value,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)::text || '%' as percentage
FROM classifications 
WHERE confidence IS NOT NULL
GROUP BY confidence

UNION ALL

-- EXPERT ACTIVITY
SELECT 
  'EXPERT ACTIVITY' as category,
  expert_id as metric,
  COUNT(*)::text as value,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)::text || '%' as percentage
FROM classifications 
WHERE expert_id IS NOT NULL
GROUP BY expert_id

UNION ALL

-- TOP TOWNS
SELECT 
  'TOP TOWNS' as category,
  town as metric,
  COUNT(*)::text as value,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)::text || '%' as percentage
FROM classifications 
GROUP BY town
)

SELECT 
  category,
  metric,
  value,
  percentage
FROM all_stats
ORDER BY 
  CASE category
    WHEN 'OVERALL SUMMARY' THEN 1
    WHEN 'TOP FLAG TYPES' THEN 2
    WHEN 'PRIMARY CATEGORIES' THEN 3
    WHEN 'DISPLAY CONTEXTS' THEN 4
    WHEN 'CONFIDENCE SCORES' THEN 5
    WHEN 'EXPERT ACTIVITY' THEN 6
    WHEN 'TOP TOWNS' THEN 7
  END,
  category, 
  metric; 