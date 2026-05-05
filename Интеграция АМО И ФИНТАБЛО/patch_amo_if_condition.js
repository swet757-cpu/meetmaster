const fs = require('fs');

const [inputPath, outputPath] = process.argv.slice(2);
const workflow = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const workflows = Array.isArray(workflow) ? workflow : [workflow];

for (const item of workflows) {
  if (item.name !== 'amoCRM → Финтабло: завершенные сделки') continue;
  const ifNode = item.nodes.find((node) => node.name === 'If');
  if (!ifNode) throw new Error('If node not found');
  const condition = ifNode.parameters?.conditions?.conditions?.[0];
  if (!condition) throw new Error('If condition not found');
  condition.leftValue = '={{ $json["body"]["leads[update][0][status_id]"] }}';
  condition.rightValue = '142';
}

fs.writeFileSync(outputPath, JSON.stringify(Array.isArray(workflow) ? workflows : workflows[0], null, 2));
