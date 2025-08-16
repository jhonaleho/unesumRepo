export interface SearchHit {
  score: number;
  titulo?: string;
  autores?: string[];
  anio_publicacion?: number | string | null;
  pagina_inicio?: number | string | null;
  pagina_fin?: number | string | null;
  pdf_url?: string | null;
  snippet?: string;
}

export interface SearchResponse {
  results: SearchHit[];
}
