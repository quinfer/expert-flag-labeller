-- Quick Data Check for Classifications Table
-- Run this first to verify you have data

SELECT 'DATA AVAILABILITY CHECK' as check_type;

SELECT 
  'Total rows in classifications table' as metric,
  COUNT(*) as value
FROM classifications;

SELECT 
  'Sample of recent classifications' as section;

SELECT 
  image_id,
  town,
  primary_category,
  specific_flag,
  confidence,
  expert_id,
  timestamp::date as date
FROM classifications 
ORDER BY timestamp DESC 
LIMIT 5;

SELECT 
  'Classification counts by expert' as section;

SELECT 
  expert_id,
  COUNT(*) as classifications
FROM classifications 
GROUP BY expert_id 
ORDER BY classifications DESC; 