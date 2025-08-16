# Thesis Search (Vite + React)

Minimal frontend for your Thesis Search API.

## Local dev

1) Create env:
```bash
cp .env.example .env.local
# edit VITE_API_BASE if needed
```

2) Install & run:
```bash
npm i
npm run dev
```

The app will call `POST {VITE_API_BASE}/search` with `{ q, top_k }`.

## Build
```bash
npm run build
npm run preview
```

## Deploy (Vercel)
- Import this project in Vercel (root = `web` if monorepo).
- Set env var: `VITE_API_BASE=https://api.yourdomain.com`.
- Deploy.
