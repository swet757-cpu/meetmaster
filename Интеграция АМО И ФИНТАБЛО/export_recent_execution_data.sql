COPY (
  SELECT "executionId", data
  FROM execution_data
  ORDER BY "executionId" DESC
  LIMIT 20
) TO STDOUT WITH (FORMAT text, DELIMITER E'\t');
