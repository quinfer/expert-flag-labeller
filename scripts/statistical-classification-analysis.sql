-- Statistical Analysis of Flag Classifications
-- Comprehensive statistical summary with statistically principled measures
-- Run this in Supabase SQL Editor to get detailed classification insights

-- ============================================================================
-- DATA AVAILABILITY CHECK
-- ============================================================================

SELECT 
  'TOTAL RECORDS CHECK' as check_type,
  COUNT(*) as total_records,
  CASE 
    WHEN COUNT(*) = 0 THEN 'NO DATA - Analysis cannot proceed'
    WHEN COUNT(*) < 10 THEN 'VERY LIMITED DATA - Results may not be meaningful'
    WHEN COUNT(*) < 100 THEN 'LIMITED DATA - Some statistics may be unreliable'
    ELSE 'SUFFICIENT DATA - Full analysis available'
  END as data_status
FROM classifications;

-- ============================================================================
-- 1. OVERVIEW STATISTICS
-- ============================================================================

SELECT 'CLASSIFICATION OVERVIEW' as analysis_section, '' as spacer, '' as spacer2;

WITH overview_stats AS (
  SELECT 
    COUNT(*) as total_classifications,
    COUNT(DISTINCT image_id) as unique_images_classified,
    COUNT(DISTINCT town) as towns_covered,
    COUNT(DISTINCT expert_id) as active_classifiers,
    COUNT(DISTINCT primary_category) as distinct_primary_categories,
    COUNT(DISTINCT specific_flag) as distinct_specific_types,
    COUNT(DISTINCT display_context) as distinct_display_contexts,
    COUNT(*) FILTER (WHERE needs_review = true) as flagged_for_review,
    MIN(timestamp) as earliest_classification,
    MAX(timestamp) as latest_classification,
    EXTRACT(DAYS FROM (MAX(timestamp) - MIN(timestamp))) as days_active
  FROM classifications
)
SELECT 
  'Total Classifications' as metric, total_classifications::text as value, '' as additional_info
FROM overview_stats
UNION ALL
SELECT 'Unique Images', unique_images_classified::text, 
  ROUND((unique_images_classified::numeric / total_classifications * 100), 1)::text || '% of total' 
FROM overview_stats
UNION ALL
SELECT 'Towns Covered', towns_covered::text, '' FROM overview_stats
UNION ALL
SELECT 'Active Classifiers', active_classifiers::text, '' FROM overview_stats
UNION ALL
SELECT 'Primary Categories', distinct_primary_categories::text, '' FROM overview_stats
UNION ALL
SELECT 'Specific Types', distinct_specific_types::text, '' FROM overview_stats
UNION ALL
SELECT 'Display Contexts', distinct_display_contexts::text, '' FROM overview_stats
UNION ALL
SELECT 'Flagged for Review', flagged_for_review::text, 
  ROUND((flagged_for_review::numeric / total_classifications * 100), 1)::text || '% of total'
FROM overview_stats
UNION ALL
SELECT 'Days Active', days_active::text, '' FROM overview_stats;

-- ============================================================================
-- 2. PRIMARY CATEGORY DISTRIBUTION WITH STATISTICAL MEASURES
-- ============================================================================

SELECT '' as separator, 'PRIMARY CATEGORY ANALYSIS' as analysis_section, '' as extra;

WITH category_stats AS (
  SELECT 
    primary_category,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage,
    AVG(confidence) as mean_confidence,
    STDDEV(confidence) as std_confidence,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) as median_confidence,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY confidence) as q1_confidence,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY confidence) as q3_confidence,
    MIN(confidence) as min_confidence,
    MAX(confidence) as max_confidence,
    COUNT(DISTINCT expert_id) as classifiers_involved,
    COUNT(*) FILTER (WHERE needs_review = true) as review_flags,
    COUNT(*) FILTER (WHERE needs_review = true) * 100.0 / COUNT(*) as review_rate
  FROM classifications 
  WHERE confidence IS NOT NULL
  GROUP BY primary_category
)
SELECT 
  primary_category,
  count,
  ROUND(percentage, 2) as percentage,
  ROUND(mean_confidence, 2) as avg_confidence,
  ROUND(std_confidence, 2) as std_confidence,
  median_confidence,
  CONCAT(q1_confidence, '-', q3_confidence) as iqr_range,
  CONCAT(min_confidence, '-', max_confidence) as range,
  classifiers_involved,
  review_flags,
  ROUND(review_rate, 2) as review_rate_percent
FROM category_stats
ORDER BY count DESC;

-- ============================================================================
-- 3. SPECIFIC FLAG TYPE ANALYSIS
-- ============================================================================

SELECT '' as separator, 'SPECIFIC FLAG TYPE ANALYSIS' as analysis_section, '' as extra;

WITH flag_analysis AS (
  SELECT 
    COALESCE(specific_flag, 'Not Specified') as flag_type,
    primary_category,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage,
    AVG(confidence) as mean_confidence,
    STDDEV(confidence) as std_confidence,
    COUNT(DISTINCT town) as towns_found,
    COUNT(DISTINCT expert_id) as classified_by,
    COUNT(*) FILTER (WHERE needs_review = true) as flagged_count
  FROM classifications
  GROUP BY specific_flag, primary_category
  HAVING COUNT(*) >= 5  -- Only show types with 5+ classifications
)
SELECT 
  flag_type,
  primary_category,
  count,
  ROUND(percentage, 2) as percentage,
  ROUND(mean_confidence, 2) as avg_confidence,
  ROUND(std_confidence, 2) as confidence_std,
  towns_found,
  classified_by,
  flagged_count
FROM flag_analysis
ORDER BY count DESC
LIMIT 20;

-- ============================================================================
-- 4. DISPLAY CONTEXT ANALYSIS
-- ============================================================================

SELECT '' as separator, 'DISPLAY CONTEXT ANALYSIS' as analysis_section, '' as extra;

WITH context_stats AS (
  SELECT 
    COALESCE(display_context, 'Not Specified') as context,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage,
    AVG(confidence) as mean_confidence,
    COUNT(DISTINCT primary_category) as categories_used,
    COUNT(DISTINCT town) as towns,
    STRING_AGG(DISTINCT primary_category, ', ' ORDER BY primary_category) as categories_list
  FROM classifications
  GROUP BY display_context
)
SELECT 
  context,
  count,
  ROUND(percentage, 2) as percentage,
  ROUND(mean_confidence, 2) as avg_confidence,
  categories_used,
  towns,
  categories_list
FROM context_stats
ORDER BY count DESC;

-- ============================================================================
-- 5. CONFIDENCE SCORE STATISTICAL ANALYSIS
-- ============================================================================

SELECT '' as separator, 'CONFIDENCE SCORE ANALYSIS' as analysis_section, '' as extra;

WITH confidence_stats AS (
  SELECT 
    confidence,
    COUNT(*) as frequency,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage,
    SUM(COUNT(*)) OVER (ORDER BY confidence) as cumulative_count
  FROM classifications
  WHERE confidence IS NOT NULL
  GROUP BY confidence
),
confidence_with_cumulative AS (
  SELECT 
    confidence,
    frequency,
    percentage,
    cumulative_count,
    cumulative_count * 100.0 / SUM(frequency) OVER () as cumulative_percentage
  FROM confidence_stats
)
SELECT 
  confidence,
  frequency,
  ROUND(percentage, 2) as percentage,
  cumulative_count,
  ROUND(cumulative_percentage, 2) as cumulative_percentage
FROM confidence_with_cumulative
ORDER BY confidence;

-- Overall confidence statistics
WITH overall_confidence AS (
  SELECT 
    COUNT(*) as n,
    AVG(confidence) as mean,
    STDDEV(confidence) as standard_deviation,
    VARIANCE(confidence) as variance,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) as median,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY confidence) as q1,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY confidence) as q3,
    MIN(confidence) as minimum,
    MAX(confidence) as maximum,
    -- Skewness approximation using Pearson's second skewness coefficient
    3 * (AVG(confidence) - PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence)) / NULLIF(STDDEV(confidence), 0) as skewness_approx
  FROM classifications
  WHERE confidence IS NOT NULL
)
SELECT 
  'Sample Size' as statistic, n::text as value
FROM overall_confidence
UNION ALL
SELECT 'Mean', ROUND(mean::numeric, 3)::text FROM overall_confidence
UNION ALL
SELECT 'Standard Deviation', ROUND(standard_deviation::numeric, 3)::text FROM overall_confidence
UNION ALL
SELECT 'Variance', ROUND(variance::numeric, 3)::text FROM overall_confidence
UNION ALL
SELECT 'Median', median::text FROM overall_confidence
UNION ALL
SELECT 'Q1 (25th percentile)', q1::text FROM overall_confidence
UNION ALL
SELECT 'Q3 (75th percentile)', q3::text FROM overall_confidence
UNION ALL
SELECT 'Interquartile Range', (q3 - q1)::text FROM overall_confidence
UNION ALL
SELECT 'Range', CONCAT(minimum, ' - ', maximum) FROM overall_confidence
UNION ALL
SELECT 'Skewness (approx)', ROUND(skewness_approx::numeric, 3)::text FROM overall_confidence;

-- ============================================================================
-- 6. GEOGRAPHIC DISTRIBUTION ANALYSIS
-- ============================================================================

SELECT '' as separator, 'GEOGRAPHIC ANALYSIS BY TOWN' as analysis_section, '' as extra;

WITH town_stats AS (
  SELECT 
    town,
    COUNT(*) as total_classifications,
    COUNT(DISTINCT image_id) as unique_images,
    COUNT(DISTINCT expert_id) as classifiers,
    COUNT(DISTINCT primary_category) as categories_found,
    AVG(confidence) as mean_confidence,
    STDDEV(confidence) as std_confidence,
    COUNT(*) FILTER (WHERE needs_review = true) as review_flags,
    COUNT(*) FILTER (WHERE needs_review = true) * 100.0 / COUNT(*) as review_rate,
    -- Most common flag type per town
    MODE() WITHIN GROUP (ORDER BY specific_flag) as most_common_flag,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage_of_total
  FROM classifications
  GROUP BY town
)
SELECT 
  town,
  total_classifications,
  unique_images,
  classifiers,
  categories_found,
  ROUND(mean_confidence, 2) as avg_confidence,
  ROUND(std_confidence, 2) as confidence_std,
  review_flags,
  ROUND(review_rate, 2) as review_rate_percent,
  most_common_flag,
  ROUND(percentage_of_total, 2) as percent_of_total
FROM town_stats
ORDER BY total_classifications DESC;

-- ============================================================================
-- 7. TEMPORAL ANALYSIS
-- ============================================================================

SELECT '' as separator, 'TEMPORAL ANALYSIS' as analysis_section, '' as extra;

-- Daily classification patterns
WITH daily_stats AS (
  SELECT 
    DATE(timestamp) as classification_date,
    COUNT(*) as daily_count,
    COUNT(DISTINCT expert_id) as active_users,
    AVG(confidence) as daily_avg_confidence,
    COUNT(DISTINCT primary_category) as categories_used,
    COUNT(*) FILTER (WHERE needs_review = true) as daily_reviews
  FROM classifications
  WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY DATE(timestamp)
)
SELECT 
  classification_date,
  daily_count,
  active_users,
  ROUND(daily_avg_confidence, 2) as avg_confidence,
  categories_used,
  daily_reviews
FROM daily_stats
ORDER BY classification_date DESC
LIMIT 14;  -- Last 14 days

-- Hourly patterns
SELECT 'HOURLY ACTIVITY PATTERNS' as pattern_type;

WITH hourly_patterns AS (
  SELECT 
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    COUNT(*) as classifications,
    COUNT(DISTINCT expert_id) as active_users,
    AVG(confidence) as avg_confidence
  FROM classifications
  WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY EXTRACT(HOUR FROM timestamp)
)
SELECT 
  hour_of_day,
  classifications,
  active_users,
  ROUND(avg_confidence, 2) as avg_confidence
FROM hourly_patterns
ORDER BY hour_of_day;

-- ============================================================================
-- 8. CLASSIFIER PERFORMANCE ANALYSIS
-- ============================================================================

SELECT '' as separator, 'CLASSIFIER PERFORMANCE ANALYSIS' as analysis_section, '' as extra;

WITH user_performance AS (
  SELECT 
    expert_id,
    COUNT(*) as total_classifications,
    COUNT(DISTINCT image_id) as unique_images,
    COUNT(DISTINCT town) as towns_worked,
    COUNT(DISTINCT primary_category) as categories_used,
    AVG(confidence) as mean_confidence,
    STDDEV(confidence) as std_confidence,
    COUNT(*) FILTER (WHERE needs_review = true) as flagged_for_review,
    COUNT(*) FILTER (WHERE needs_review = true) * 100.0 / COUNT(*) as review_rate,
    MIN(timestamp) as first_classification,
    MAX(timestamp) as last_classification,
    EXTRACT(DAYS FROM (MAX(timestamp) - MIN(timestamp))) + 1 as days_active,
    COUNT(*) / (EXTRACT(DAYS FROM (MAX(timestamp) - MIN(timestamp))) + 1) as avg_daily_rate
  FROM classifications
  WHERE expert_id IS NOT NULL
  GROUP BY expert_id
  HAVING COUNT(*) >= 10  -- Only users with 10+ classifications
)
SELECT 
  expert_id,
  total_classifications,
  unique_images,
  towns_worked,
  categories_used,
  ROUND(mean_confidence, 2) as avg_confidence,
  ROUND(std_confidence, 2) as confidence_std,
  flagged_for_review,
  ROUND(review_rate, 2) as review_rate_percent,
  first_classification::date as first_active,
  last_classification::date as last_active,
  days_active,
  ROUND(avg_daily_rate, 1) as daily_classification_rate
FROM user_performance
ORDER BY total_classifications DESC;

-- ============================================================================
-- 9. QUALITY METRICS AND ANOMALY DETECTION
-- ============================================================================

SELECT '' as separator, 'QUALITY METRICS & ANOMALIES' as analysis_section, '' as extra;

-- Potential data quality issues
WITH quality_checks AS (
  SELECT 
    'Missing specific_flag when primary_category specified' as issue_type,
    COUNT(*) as count
  FROM classifications 
  WHERE primary_category IS NOT NULL AND (specific_flag IS NULL OR specific_flag = '')
  
  UNION ALL
  
  SELECT 
    'Missing display_context',
    COUNT(*)
  FROM classifications 
  WHERE display_context IS NULL OR display_context = ''
  
  UNION ALL
  
  SELECT 
    'Confidence score outside expected range (1-5)',
    COUNT(*)
  FROM classifications 
  WHERE confidence IS NOT NULL AND (confidence < 1 OR confidence > 5)
  
  UNION ALL
  
  SELECT 
    'Unusually long user_content (>200 chars)',
    COUNT(*)
  FROM classifications 
  WHERE LENGTH(user_content) > 200
  
  UNION ALL
  
  SELECT 
    'Same image classified multiple times by same user',
    COUNT(*)
  FROM (
    SELECT image_id, expert_id, COUNT(*) as dupe_count
    FROM classifications
    GROUP BY image_id, expert_id
    HAVING COUNT(*) > 1
  ) duplicates
)
SELECT issue_type, count
FROM quality_checks
WHERE count > 0;

-- Outlier analysis for confidence scores by category
WITH category_stats AS (
  SELECT 
    primary_category,
    confidence,
    AVG(confidence) OVER (PARTITION BY primary_category) as mean_confidence,
    STDDEV(confidence) OVER (PARTITION BY primary_category) as std_confidence
  FROM classifications
  WHERE confidence IS NOT NULL
),
outlier_analysis AS (
  SELECT 
    primary_category,
    mean_confidence,
    std_confidence,
    CASE WHEN ABS(confidence - mean_confidence) > 2 * std_confidence THEN 1 ELSE 0 END as is_outlier
  FROM category_stats
),
confidence_outliers AS (
  SELECT 
    primary_category,
    COUNT(*) as total_count,
    AVG(mean_confidence) as mean_confidence,
    AVG(std_confidence) as std_confidence,
    SUM(is_outlier) as outliers
  FROM outlier_analysis
  GROUP BY primary_category
  HAVING COUNT(*) >= 10
)
SELECT 
  primary_category,
  total_count,
  ROUND(mean_confidence, 2) as mean_confidence,
  ROUND(std_confidence, 2) as std_confidence,
  outliers,
  ROUND(outliers * 100.0 / total_count, 2) as outlier_percentage
FROM confidence_outliers
ORDER BY outlier_percentage DESC;

-- ============================================================================
-- 10. STATISTICAL SUMMARY REPORT
-- ============================================================================

SELECT '' as separator, 'FINAL STATISTICAL SUMMARY' as analysis_section, '' as extra;

WITH final_summary AS (
  SELECT 
    COUNT(*) as n,
    COUNT(DISTINCT image_id) as unique_images,
    COUNT(DISTINCT town) as towns,
    COUNT(DISTINCT expert_id) as classifiers,
    -- Mode calculation for categorical variables
    MODE() WITHIN GROUP (ORDER BY primary_category) as most_common_category,
    MODE() WITHIN GROUP (ORDER BY specific_flag) as most_common_flag,
    MODE() WITHIN GROUP (ORDER BY display_context) as most_common_context,
    -- Central tendency for confidence
    AVG(confidence) as mean_confidence,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) as median_confidence,
    -- Variability measures
    STDDEV(confidence) as confidence_std,
    VARIANCE(confidence) as confidence_variance,
    -- Quality indicators
    COUNT(*) FILTER (WHERE needs_review = true) * 100.0 / COUNT(*) as review_rate,
    COUNT(*) FILTER (WHERE confidence >= 4) * 100.0 / COUNT(*) as high_confidence_rate,
    -- Coverage metrics
    COUNT(DISTINCT CONCAT(primary_category, '|', specific_flag)) as unique_flag_combinations,
    COUNT(DISTINCT CONCAT(primary_category, '|', display_context)) as unique_category_context_combinations
  FROM classifications
)
SELECT 
  'Total Sample Size' as metric, n::text as value
FROM final_summary
UNION ALL
SELECT 'Coverage: Unique Images', unique_images::text FROM final_summary
UNION ALL
SELECT 'Coverage: Towns', towns::text FROM final_summary
UNION ALL
SELECT 'Coverage: Classifiers', classifiers::text FROM final_summary
UNION ALL
SELECT 'Most Common Category', most_common_category FROM final_summary
UNION ALL
SELECT 'Most Common Flag Type', most_common_flag FROM final_summary
UNION ALL
SELECT 'Most Common Display Context', most_common_context FROM final_summary
UNION ALL
SELECT 'Mean Confidence Score', ROUND(mean_confidence::numeric, 3)::text FROM final_summary
UNION ALL
SELECT 'Median Confidence Score', median_confidence::text FROM final_summary
UNION ALL
SELECT 'Confidence Standard Deviation', ROUND(confidence_std::numeric, 3)::text FROM final_summary
UNION ALL
SELECT 'Review Rate (%)', ROUND(review_rate, 2)::text FROM final_summary
UNION ALL
SELECT 'High Confidence Rate (4-5) (%)', ROUND(high_confidence_rate, 2)::text FROM final_summary
UNION ALL
SELECT 'Unique Flag Combinations', unique_flag_combinations::text FROM final_summary
UNION ALL
SELECT 'Unique Category-Context Pairs', unique_category_context_combinations::text FROM final_summary;

-- End of Statistical Analysis
SELECT 'Analysis Complete - ' || CURRENT_TIMESTAMP::text as completion_timestamp; 