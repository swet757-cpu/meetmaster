const fs = require('fs');

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error('Usage: node patch_amo_fintablo_dedupe.js input.json output.json');
  process.exit(2);
}

const raw = fs.readFileSync(inputPath, 'utf8');
const parsed = JSON.parse(raw);
const workflows = Array.isArray(parsed) ? parsed : [parsed];

for (const workflow of workflows) {
  if (!workflow.name || !workflow.name.includes('amoCRM')) continue;

  workflow.nodes = workflow.nodes.filter((node) => ![
    'Антидубль по ID сделки AMO',
    'Проверить дубль по ID сделки AMO',
    'Запомнить ID сделки AMO'
  ].includes(node.name));
  delete workflow.connections['Антидубль по ID сделки AMO'];
  delete workflow.connections['Проверить дубль по ID сделки AMO'];
  delete workflow.connections['Запомнить ID сделки AMO'];

  const ifNode = workflow.nodes.find((node) => node.name === 'If');
  const httpNode = workflow.nodes.find((node) => node.name === 'HTTP Request');
  if (!ifNode || !httpNode) {
    throw new Error('Не найдены узлы If или HTTP Request');
  }

  const checkNode = {
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
        "  freshItems.push(item);",
        "}",
        "",
        "return freshItems;"
      ].join('\n')
    },
    id: 'amo-deal-dedupe-check-code',
    name: 'Проверить дубль по ID сделки AMO',
    type: 'n8n-nodes-base.code',
    typeVersion: 2,
    position: [
      Math.round((ifNode.position[0] + httpNode.position[0]) / 2),
      Math.round((ifNode.position[1] + httpNode.position[1]) / 2)
    ]
  };

  const rememberNode = {
    parameters: {
      jsCode: [
        "const store = $getWorkflowStaticData('global');",
        "if (!store.sentAmoDealIds) {",
        "  store.sentAmoDealIds = {};",
        "}",
        "",
        "for (const item of items) {",
        "  const leadId = item.json?.body?.['leads[update][0][id]'];",
        "  if (leadId) {",
        "    store.sentAmoDealIds[String(leadId)] = new Date().toISOString();",
        "  }",
        "}",
        "",
        "return items;"
      ].join('\n')
    },
    id: 'amo-deal-dedupe-remember-code',
    name: 'Запомнить ID сделки AMO',
    type: 'n8n-nodes-base.code',
    typeVersion: 2,
    position: [
      httpNode.position[0] + 260,
      httpNode.position[1]
    ]
  };

  workflow.nodes.push(checkNode, rememberNode);
  workflow.connections.If = {
    main: [
      [
        {
          node: 'Проверить дубль по ID сделки AMO',
          type: 'main',
          index: 0
        }
      ],
      []
    ]
  };
  workflow.connections['Проверить дубль по ID сделки AMO'] = {
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
  workflow.connections['HTTP Request'] = {
    main: [
      [
        {
          node: 'Запомнить ID сделки AMO',
          type: 'main',
          index: 0
        }
      ]
    ]
  };
}

fs.writeFileSync(outputPath, JSON.stringify(Array.isArray(parsed) ? workflows : workflows[0], null, 2));
