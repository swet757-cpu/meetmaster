const fs = require('fs');

function reviveFlatted(text) {
  const table = JSON.parse(text);
  const seen = new Map();
  const fromRef = (ref) => {
    const index = Number(ref);
    const value = table[index];
    if (value === null || typeof value !== 'object') return value;
    if (seen.has(index)) return seen.get(index);
    const out = Array.isArray(value) ? [] : {};
    seen.set(index, out);
    if (Array.isArray(value)) {
      for (const item of value) out.push(resolve(item));
    } else {
      for (const [key, item] of Object.entries(value)) out[key] = resolve(item);
    }
    return out;
  };
  const resolve = (value) => {
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) < table.length) return fromRef(value);
    return value;
  };
  return fromRef(0);
}

const input = fs.readFileSync(process.argv[2], 'utf8').trim();
const byLead = new Map();

for (const line of input.split(/\r?\n/).filter(Boolean)) {
  const tab = line.indexOf('\t');
  const executionId = line.slice(0, tab);
  const dataText = line.slice(tab + 1);
  const decoded = reviveFlatted(dataText);
  const runData = decoded?.resultData?.runData || {};
  const nodes = Object.keys(runData);
  const webhookRun = runData.Webhook?.[0];
  const body = webhookRun?.data?.main?.[0]?.[0]?.json?.body || {};
  const leadId = body['leads[update][0][id]'];
  const statusId = body['leads[update][0][status_id]'];
  if (!leadId || String(statusId) !== '142') continue;
  const item = byLead.get(String(leadId)) || {
    leadId: String(leadId),
    name: body['leads[update][0][name]'] || '',
    amount: body['leads[update][0][price]'] || '',
    pipelineId: body['leads[update][0][pipeline_id]'] || '',
    executions: [],
    hasHttpRequest: false,
    body
  };
  item.executions.push(executionId);
  if (nodes.includes('HTTP Request')) item.hasHttpRequest = true;
  if (body['leads[update][0][name]']) item.name = body['leads[update][0][name]'];
  if (body['leads[update][0][price]']) item.amount = body['leads[update][0][price]'];
  byLead.set(String(leadId), item);
}

for (const item of byLead.values()) {
  console.log(JSON.stringify({
    leadId: item.leadId,
    name: item.name,
    amount: item.amount,
    pipelineId: item.pipelineId,
    executions: item.executions,
    hasHttpRequest: item.hasHttpRequest
  }));
}
