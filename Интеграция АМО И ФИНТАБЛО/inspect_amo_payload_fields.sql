SELECT
  "executionId",
  regexp_matches(data, 'leads\[update\]\[0\]\[id\]"[^"]*"([^"]+)"', 'g') AS lead_id_matches,
  regexp_matches(data, 'leads\[update\]\[0\]\[status_id\]"[^"]*"([^"]+)"', 'g') AS status_id_matches,
  regexp_matches(data, 'leads\[update\]\[0\]\[pipeline_id\]"[^"]*"([^"]+)"', 'g') AS pipeline_id_matches
FROM execution_data
ORDER BY "executionId" DESC
LIMIT 10;
