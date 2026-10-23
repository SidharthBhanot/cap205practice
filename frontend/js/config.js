// Normally FastAPI serves /app on the same origin. A separately served frontend
// uses the same machine on port 8000, rather than always addressing loopback.
// For a custom backend, set <meta name="api-base" content="http://localhost:9000">
// in the frontend HTML. This changes routing only; it does not start a backend.
export function resolveApiBase(page, configured = '') {
  if (configured.trim()) {
    const url = new URL(configured.trim(), page.href);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
      throw new Error('API base must be an HTTP(S) URL without credentials.');
    }
    return url.href.replace(/\/$/, '');
  }
  if (page.pathname.startsWith('/app/')) return page.origin;
  const hostname = page.hostname || '127.0.0.1';
  return `http://${hostname}:8000`;
}

export const API_BASE = resolveApiBase(location,
  document.querySelector('meta[name="api-base"]')?.content || '');
