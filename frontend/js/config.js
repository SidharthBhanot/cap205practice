// The backend serves the UI at /app. For python -m http.server 5500,
// use the explicitly configured local API below. No portal is connected.
export const API_BASE = location.pathname.startsWith('/app/')
  ? location.origin : 'http://127.0.0.1:8000';
