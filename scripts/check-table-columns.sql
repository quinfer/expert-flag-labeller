-- Show all column names in the classifications table
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'classifications'
ORDER BY ordinal_position;

-- Alternative: Show first few rows to see headers and data
SELECT * FROM classifications LIMIT 3; 