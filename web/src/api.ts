import type { SearchResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function search(q: string, top_k = 10, signal?: AbortSignal) {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ q, top_k }),
    signal
  });
  return handle<SearchResponse>(res);
}
