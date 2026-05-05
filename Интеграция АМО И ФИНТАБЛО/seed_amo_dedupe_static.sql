UPDATE workflow_entity
SET "staticData" =
  COALESCE("staticData"::jsonb, '{}'::jsonb)
  || jsonb_build_object(
    'global',
    COALESCE(("staticData"::jsonb -> 'global'), '{}'::jsonb)
    || jsonb_build_object(
      'sentAmoDealIds',
      COALESCE(("staticData"::jsonb -> 'global' -> 'sentAmoDealIds'), '{}'::jsonb)
      || jsonb_build_object(
        '26141561', to_jsonb(now()::text),
        '26153041', to_jsonb(now()::text),
        '26141713', to_jsonb(now()::text),
        '26141887', to_jsonb(now()::text),
        '26152837', to_jsonb(now()::text)
      )
    )
  )
WHERE id = '9sjdTrPk9C33LWPB';

SELECT "staticData"::jsonb -> 'global' -> 'sentAmoDealIds' AS sent_amo_deal_ids
FROM workflow_entity
WHERE id = '9sjdTrPk9C33LWPB';
