import { useEffect, useMemo, useRef, useState } from 'react'
import { search } from './api'
import type { SearchHit } from './types'

function useDebounced<T>(value: T, ms = 400) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

export default function App() {
  const [q, setQ] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<SearchHit[]>([]);
  const controllerRef = useRef<AbortController | null>(null);
  const debouncedQ = useDebounced(q, 200);

  const canSearch = useMemo(() => debouncedQ.trim().length > 0, [debouncedQ]);

  async function doSearch() {
    if (!canSearch) return;
    controllerRef.current?.abort();
    const c = new AbortController();
    controllerRef.current = c;
    setLoading(true);
    setError(null);
     try {
    const { results } = await search(debouncedQ, 10, { signal: c.signal });
    setResults(results);
  } catch (e: any) {
    // ⬇️ Ignore cancellations triggered by typing
    if (e?.name === 'AbortError' || String(e?.message || '').toLowerCase().includes('aborted')) {
      return;
    }
    setError(e?.message ?? 'Search failed');
  } finally {
    setLoading(false);
  }

  }

  useEffect(() => { doSearch(); }, [debouncedQ]);

  return (
    <div style={{ maxWidth: 960, margin: '2rem auto', padding: '0 1rem' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Buscar Tesis en UnesumRepo</h1>
        <span style={{ opacity: 0.75, fontSize: '0.9rem' }}>Vite + React</span>
        <span style={{ opacity: 0.75, fontSize: '0.5rem' }}>by Jhon Alejandro</span>
      </header>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Pregunta acerca de una tesis"
          autoFocus
          style={{
            flex: 1,
            padding: '0.75rem 0.9rem',
            borderRadius: 10,
            border: '1px solid rgba(127,127,127,0.35)',
            outline: 'none'
          }}
        />
      </div>

      <div style={{ marginTop: '1rem', minHeight: 24 }}>
        {loading && <span>Buscando</span>}
        {error && <span role="alert" style={{ color: 'tomato' }}>{error}</span>}
        {!loading && !error && results.length === 0 && canSearch && (
          <span>Sin Resultados.</span>
        )}
      </div>

      <ul style={{ marginTop: '1rem', listStyle: 'none', padding: 0 }}>
        {results.map((r, i) => (
          <li key={i} style={{
            border: '1px solid rgba(127,127,127,0.25)',
            borderRadius: 12,
            padding: '0.9rem 1rem',
            marginBottom: '0.75rem',
            background: 'rgba(127,127,127,0.05)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem' }}>
              <strong style={{ fontSize: '1.05rem' }}>
                {r.titulo || 'Untitled'} {r.anio_publicacion ? `(${r.anio_publicacion})` : ''}
              </strong>
              <span style={{ fontVariantNumeric: 'tabular-nums', opacity: 0.75 }}>score: {r.score.toFixed(3)}</span>
            </div>
            <div style={{ marginTop: 4, opacity: 0.8, fontSize: '0.95rem' }}>
              {(r.autores || []).join(', ') || <em>Autor Desconocido</em>}
            </div>
            <div style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>
              {r.snippet || ''}
            </div>
            <div style={{ marginTop: 8 }}>
              {r.pdf_url && <a href={r.pdf_url} target="_blank" rel="noreferrer">Abrir PDF</a>}
              {(r.pagina_inicio != null || r.pagina_fin != null) && (
                <span style={{ marginLeft: 12, opacity: 0.8 }}>
                  Paginas: {r.pagina_inicio ?? '?'}–{r.pagina_fin ?? '?'}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>

      <footer style={{ marginTop: '2rem', opacity: 0.7, fontSize: '0.9rem' }}>
        API: <code>{import.meta.env.VITE_API_BASE ?? '(same origin)'}</code>

      </footer>
    </div>
  )
}
