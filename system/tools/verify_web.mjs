// Dependency-free unit checks for the shipped request helper, not a browser-QA substitute.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = fs.readFileSync(path.join(root, 'src/main/resources/web/app.js'), 'utf8');
const start = source.indexOf('async function api(');
const end = source.indexOf('\nfunction errorBox(', start);
assert(start >= 0 && end > start);
const results = [];
const reply = (ok = true, status = 200, body = { ok: true }) => ({
  ok, status, json: async () => body, headers: { get: () => 'header-request-id' },
});

async function run(name, test) {
  const calls = [];
  let behavior;
  const context = vm.createContext({
    state: { csrf: 'synthetic-csrf' }, T: (zh) => zh,
    crypto: { randomUUID: () => 'synthetic-stable-receipt-key' },
    setTimeout: (resolve) => { resolve(); return 1; },
    fetch: async (url, options) => {
      calls.push({ url, options: JSON.parse(JSON.stringify(options)) });
      return behavior(calls.length);
    },
  });
  vm.runInContext(source.slice(start, end), context);
  await test(context.api, calls, (fn) => { behavior = fn; });
  results.push({ name, passed: true });
  console.log('PASS', name);
}

await run('Lost business response retries once with unchanged receipt, body and CSRF', async (api, calls, set) => {
  set((n) => { if (n === 1) throw new TypeError('synthetic disconnection'); return reply(); });
  await api('/finance/periods', { action: 'expense', amount_fen: 100 });
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[0], calls[1]);
});
await run('Repeated connection loss stops after one retry and warns of uncertain result', async (api, calls, set) => {
  set(() => { throw new TypeError('synthetic disconnection'); });
  await assert.rejects(api('/patients', { name_zh: '合成记录' }), (e) => e.code === 'CONNECTION_INTERRUPTED' && e.message.includes('核对'));
  assert.equal(calls.length, 2);
});
await run('Password login is never automatically replayed', async (api, calls, set) => {
  set(() => { throw new TypeError('synthetic disconnection'); });
  await assert.rejects(api('/auth/login', { username: 'synthetic', password: 'not-a-real-password' }));
  assert.equal(calls.length, 1);
});
await run('HTTP conflict is not retried and preserves diagnostic request ID', async (api, calls, set) => {
  set(() => reply(false, 409, { error: { code: 'VERSION_CONFLICT', message: '记录已变化', request_id: 'synthetic-request-id' } }));
  await assert.rejects(api('/appointments/example', { action: 'cancel' }), (e) => e.status === 409 && e.requestId === 'synthetic-request-id');
  assert.equal(calls.length, 1);
});
await run('Cold-start non-JSON response gives a readable message', async (api, calls, set) => {
  set(() => ({ ...reply(false, 502), json: async () => { throw new SyntaxError('synthetic HTML'); } }));
  await assert.rejects(api('/dashboard'), (e) => e.message.includes('启动'));
  assert.equal(calls.length, 1);
});
await run('Read-only disconnection retries without creating a mutation', async (api, calls, set) => {
  set((n) => { if (n === 1) throw new TypeError('synthetic disconnection'); return reply(); });
  await api('/portal');
  assert.equal(calls.length, 2);
  assert.equal(calls[1].options.method, 'GET');
  assert.equal(calls[1].options.headers['Idempotency-Key'], undefined);
});

fs.writeFileSync(path.join(root, 'qa/web-request-tests.json'), JSON.stringify({
  passed: true, tests: results.length, method: 'Node VM unit tests against the shipped api helper',
  source_sha256: createHash('sha256').update(source).digest('hex'),
  browser_interaction_verified: false, results,
}, null, 2) + '\n');
console.log('PASS', results.length, 'web-request unit checks; browser interactions remain separately verified.');
