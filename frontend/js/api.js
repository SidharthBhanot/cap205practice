import { API_BASE } from './config.js';

export async function api(path, { method = 'GET', body, ...rest } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    let response;
    try {
      response = await fetch(API_BASE + path, {
        method, headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal, ...rest
      });
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      throw new Error(`Cannot reach the API at ${API_BASE}. Start FastAPI, then retry. If the frontend runs separately, check its API address and allowed origin.`);
    }
    if (response.status === 204) return null;
    if (!(response.headers.get('content-type') || '').toLowerCase().includes('application/json')) {
      throw new Error(`The server at ${API_BASE} returned a non-JSON response (HTTP ${response.status}). Open the app through the FastAPI server; a static file server cannot provide the API.`);
    }
    let data;
    try { data = await response.json(); }
    catch { throw new Error('The API returned invalid JSON. Check the backend terminal and retry.'); }
    if (!response.ok) {
      const detail = data?.detail;
      throw new Error(Array.isArray(detail)
        ? detail.map(e => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`).join('\n')
        : typeof detail === 'string' ? detail : `Request failed (${response.status}).`);
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request timed out. Check the API before trying again.');
    throw error;
  } finally { clearTimeout(timer); }
}

export function params(values) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) if (value !== '' && value !== undefined && value !== null) query.set(key, value);
  return '?' + query.toString();
}
