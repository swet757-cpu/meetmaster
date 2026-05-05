COPY (
  SELECT "executionId", data
  FROM execution_data
  ORDER BY "executionId" DESC
) TO STDOUT WITH (FORMAT text, DELIMITER E'\t');
