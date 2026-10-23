// Optional authoring checks: node --test frontend/tests/api.test.mjs (Node 18+).
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

globalThis.location = new URL('http://localhost:9000/app/sources.html');
globalThis.document = { querySelector: () => null };
const moduleFrom = source => import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const config = await moduleFrom(await readFile(new URL('../js/config.js', import.meta.url), 'utf8'));
const source = await readFile(new URL('../js/api.js', import.meta.url), 'utf8');
const { api } = await moduleFrom(source.replace("import { API_BASE } from './config.js';", "const API_BASE = 'http://localhost:9000';"));

test('API routing preserves the served app port and separate frontend hostname', () => {
  assert.equal(config.API_BASE, 'http://localhost:9000');
  assert.equal(config.resolveApiBase(new URL('http://192.168.1.10:5500/sources.html')), 'http://192.168.1.10:8000');
  assert.equal(config.resolveApiBase(location, 'http://localhost:8100/'), 'http://localhost:8100');
  assert.throws(() => config.resolveApiBase(location, 'javascript:alert(1)'));
});

test('request failures explain the endpoint and successful retries return data', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => { throw new TypeError('Failed to fetch'); };
    await assert.rejects(api('/sources'), /Cannot reach the API at http:\/\/localhost:9000/);
    globalThis.fetch = async () => new Response('<html>Static server</html>', { headers: { 'content-type': 'text/html' } });
    await assert.rejects(api('/sources'), /non-JSON response/);
    globalThis.fetch = async () => new Response('{', { headers: { 'content-type': 'application/json' } });
    await assert.rejects(api('/sources'), /invalid JSON/);
    globalThis.fetch = async () => new Response('[]', { headers: { 'content-type': 'application/json' } });
    assert.deepEqual(await api('/sources'), []);
    globalThis.fetch = async () => new Response('{"detail":"Source not found"}', { status: 404, headers: { 'content-type': 'application/json' } });
    await assert.rejects(api('/sources/99'), /Source not found/);
  } finally { globalThis.fetch = original; }
});
