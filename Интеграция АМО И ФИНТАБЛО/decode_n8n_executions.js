const fs = require('fs');

function reviveFlatted(text) {
  const table = JSON.parse(text);
  const seen = new Map();

  function fromRef(ref) {
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
  }

  function resolve(value) {
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) < table.length) {
      return fromRef(value);
    }
    return value;
  }

  return fromRef(0);
}

const input = fs.readFileSync(process.argv[2], 'utf8').trim();
for (const line of input.split(/\r?\n/).filter(Boolean)) {
  const tab = line.indexOf('\t');
  const executionId = line.slice(0, tab);
  const dataText = line.slice(tab + 1);
  const decoded = reviveFlatted(dataText);
  const runData = decoded?.resultData?.runData || {};
  const nodes = Object.keys(runData);
  const webhookRun = runData.Webhook?.[0];
  const body = webhookRun?.data?.main?.[0]?.[0]?.json?.body || {};

  const get = (key) => body[key] ?? '';
  console.log([
    executionId,
    nodes.join(' -> '),
    get('leads[update][0][id]'),
    get('leads[update][0][status_id]'),
    get('leads[update][0][pipeline_id]'),
    get('leads[update][0][price]'),
    String(get('leads[update][0][name]')).slice(0, 80)
  ].join('\t'));
}
