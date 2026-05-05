SELECT "executionId", length(data), left(data, 500)
FROM execution_data
ORDER BY "executionId" DESC
LIMIT 1;
