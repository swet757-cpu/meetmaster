const fs = require('fs');

const [inputPath, outputPath] = process.argv.slice(2);
const raw = fs.readFileSync(inputPath, 'utf8');
const parsed = JSON.parse(raw);
const workflows = Array.isArray(parsed) ? parsed : [parsed];

for (const workflow of workflows) {
  if (workflow.name !== 'amoCRM → Финтабло: завершенные сделки') continue;

  const ifNode = workflow.nodes.find((node) => node.name === 'If');
  const httpNode = workflow.nodes.find((node) => node.name === 'HTTP Request');
  if (!ifNode || !httpNode) throw new Error('Не найдены If или HTTP Request');

  const condition = ifNode.parameters?.conditions?.conditions?.[0];
  if (!condition) throw new Error('Не найдено условие If');
  condition.leftValue = '={{ $json["body"]["leads[update][0][status_id]"] }}';
  condition.rightValue = '142';

  workflow.nodes = workflow.nodes.filter((node) => ![
    'Антидубль по ID сделки AMO',
    'Проверить дубль по ID сделки AMO',
    'Запомнить ID сделки AMO'
  ].includes(node.name));

  delete workflow.connections['Антидубль по ID сделки AMO'];
  delete workflow.connections['Проверить дубль по ID сделки AMO'];
  delete workflow.connections['Запомнить ID сделки AMO'];
  delete workflow.connections['HTTP Request'];

  const dedupeNode = {
    parameters: {
      jsCode: [
        "const store = $getWorkflowStaticData('global');",
        "if (!store.sentAmoDealIds) {",
        "  store.sentAmoDealIds = {};",
        "}",
        "",
        "const freshItems = [];",
        "for (const item of items) {",
        "  const leadId = item.json?.body?.['leads[update][0][id]'];",
        "  if (!leadId) {",
        "    freshItems.push(item);",
        "    continue;",
        "  }",
        "",
        "  const key = String(leadId);",
        "  if (store.sentAmoDealIds[key]) {",
        "    continue;",
        "  }",
        "",
        "  store.sentAmoDealIds[key] = new Date().toISOString();",
        "  freshItems.push(item);",
        "}",
        "",
        "return freshItems;"
      ].join('\n')
    },
    id: 'amo-deal-dedupe-code',
    name: 'Проверить и запомнить ID сделки AMO',
    type: 'n8n-nodes-base.code',
    typeVersion: 2,
    position: [
      Math.round((ifNode.position[0] + httpNode.position[0]) / 2),
      Math.round((ifNode.position[1] + httpNode.position[1]) / 2)
    ]
  };

  workflow.nodes.push(dedupeNode);
  workflow.connections.If = {
    main: [
      [
        {
          node: 'Проверить и запомнить ID сделки AMO',
          type: 'main',
          index: 0
        }
      ],
      []
    ]
  };
  workflow.connections['Проверить и запомнить ID сделки AMO'] = {
    main: [
      [
        {
          node: 'HTTP Request',
          type: 'main',
          index: 0
        }
      ]
    ]
  };
}

fs.writeFileSync(outputPath, JSON.stringify(Array.isArray(parsed) ? workflows : workflows[0], null, 2));
