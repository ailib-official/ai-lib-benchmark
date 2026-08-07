#!/usr/bin/env node
/**
 * Client-path latency runner (ai-lib-ts AiClient → mock). GOV-007 Bench B.
 */
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import path from 'node:path';
import process from 'node:process';

const mockUrl = (process.env.MOCK_HTTP_URL || 'http://127.0.0.1:4010').replace(/\/$/, '');
const samples = Number(process.env.SAMPLES || '5');
const tsRoot = process.env.AI_LIB_TS_ROOT;

async function loadApi() {
  if (tsRoot) {
    const entry = path.join(tsRoot, 'src', 'index.ts');
    return import(pathToFileURL(entry).href);
  }
  const require = createRequire(import.meta.url);
  return import(require.resolve('ai-lib-ts'));
}

const { Message, createClientBuilder } = await loadApi();

const latencies = [];
let errors = 0;

for (let i = 0; i < samples; i++) {
  const t0 = performance.now();
  try {
    const client = await createClientBuilder()
      .withMockServer(mockUrl)
      .withTimeout(15000)
      .build('openai/gpt-4o');
    const response = await client
      .chat([Message.user('Hello')])
      .maxTokens(64)
      .execute();
    if (!response?.content) errors += 1;
  } catch (e) {
    errors += 1;
    console.error('error:', e);
  }
  latencies.push(performance.now() - t0);
}

const mean = latencies.reduce((a, b) => a + b, 0) / latencies.length;
const result = {
  harness: 'client-path-mock',
  runtime: 'ai-lib-ts',
  path: 'createClientBuilder.chat.execute',
  mock_url: mockUrl,
  model: 'openai/gpt-4o',
  samples,
  ok: samples - errors,
  errors,
  latency_ms: {
    mean: Number(mean.toFixed(2)),
    min: Number(Math.min(...latencies).toFixed(2)),
    max: Number(Math.max(...latencies).toFixed(2)),
  },
};

console.log(JSON.stringify(result, null, 2));
if (errors) process.exit(1);
