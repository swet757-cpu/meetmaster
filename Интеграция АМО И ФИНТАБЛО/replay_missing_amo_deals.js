const fs = require('fs');
const http = require('http');

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

function postWebhook(body) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);
    const req = http.request({
      hostname: '127.0.0.1',
      port: 5678,
      path: '/webhook/amocrm-fintablo-deal',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 20000
    }, (res) => {
      res.resume();
      res.on('end', () => resolve(res.statusCode));
    });
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy(new Error('timeout'));
    });
    req.end(payload);
  });
}

async function main() {
  const input = fs.readFileSync(process.argv[2], 'utf8').trim();
  const byLead = new Map();

  for (const line of input.split(/\r?\n/).filter(Boolean)) {
    const tab = line.indexOf('\t');
    const executionId = line.slice(0, tab);
    const decoded = reviveFlatted(line.slice(tab + 1));
    const runData = decoded?.resultData?.runData || {};
    const nodes = Object.keys(runData);
    const body = runData.Webhook?.[0]?.data?.main?.[0]?.[0]?.json?.body || {};
    const leadId = body['leads[update][0][id]'];
    const statusId = body['leads[update][0][status_id]'];
    if (!leadId || String(statusId) !== '142') continue;

    const key = String(leadId);
    const current = byLead.get(key);
    const item = current || { body, executions: [], hasHttpRequest: false };
    item.executions.push(executionId);
    if (nodes.includes('HTTP Request')) item.hasHttpRequest = true;
    if (!current || Number(executionId) > Number(current.executions[0])) item.body = body;
    byLead.set(key, item);
  }

  const missing = [...byLead.entries()]
    .filter(([, item]) => !item.hasHttpRequest)
    .sort((a, b) => Number(a[0]) - Number(b[0]));

  for (const [leadId, item] of missing) {
    const status = await postWebhook(item.body);
    console.log(`${leadId}\t${item.body['leads[update][0][price]'] || ''}\t${item.body['leads[update][0][name]'] || ''}\tHTTP ${status}`);
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
