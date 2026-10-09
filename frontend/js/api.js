import { API_BASE } from './config.js';

export async function api(path, { method = 'GET', body, ...rest } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(API_BASE + path, {
      method, headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal, ...rest
    });
    if (response.status === 204) return null;
    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail;
      throw new Error(Array.isArray(detail)
        ? detail.map(e => `${e.loc.slice(1).join('.')}: ${e.msg}`).join('\n')
        : detail || `Request failed (${response.status}).`);
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request timed out. Check the API before trying again.');
    if (error instanceof TypeError) throw new Error('Cannot reach the API. Start FastAPI at http://127.0.0.1:8000 and reload.');
    throw error;
  } finally { clearTimeout(timer); }
}

export function params(values) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) if (value !== '' && value !== undefined && value !== null) query.set(key, value);
  return '?' + query.toString();
}
