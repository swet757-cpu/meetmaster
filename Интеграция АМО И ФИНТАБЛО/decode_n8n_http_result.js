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
for (const line of input.split(/\r?\n/).filter(Boolean)) {
  const tab = line.indexOf('\t');
  const executionId = line.slice(0, tab);
  const decoded = reviveFlatted(line.slice(tab + 1));
  const runData = decoded?.resultData?.runData || {};
  const nodes = Object.keys(runData);
  if (!nodes.includes('HTTP Request')) continue;
  const httpRun = runData['HTTP Request']?.[0] || {};
  const error = httpRun.error ? JSON.stringify(httpRun.error).slice(0, 300) : '';
  const output = httpRun.data?.main?.[0]?.[0]?.json || {};
  console.log(JSON.stringify({
    executionId,
    nodes,
    error: error || null,
    outputKeys: Object.keys(output),
    outputPreview: JSON.stringify(output).slice(0, 500)
  }, null, 2));
}
