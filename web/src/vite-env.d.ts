/// <reference types="vite/client" />

// (opcional) declara tu variable para autocompletado y type-safety
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
