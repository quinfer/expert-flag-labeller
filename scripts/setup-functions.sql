-- Function Definitions - Run after tables are created
-- Run this in the Supabase SQL Editor

-- Create a stored procedure for generating classification summaries
CREATE OR REPLACE FUNCTION summarize_classifications()
RETURNS TABLE (
  category TEXT,
  count BIGINT,
  percentage NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH total AS (SELECT COUNT(*) as total_count FROM classifications)
  SELECT 
    primary_category, 
    COUNT(*) as count,
    CASE 
      WHEN (SELECT total_count FROM total) > 0 THEN 
        ROUND((COUNT(*) * 100.0 / (SELECT total_count FROM total)), 2)
      ELSE 0
    END as percentage
  FROM 
    classifications
  GROUP BY 
    primary_category
  ORDER BY 
    count DESC;
END;
$$;