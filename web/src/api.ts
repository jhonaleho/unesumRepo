// web/src/api.ts
import type { SearchResponse } from "./types";

/** ===== Config ===== */
const RAW_BASE = import.meta.env.VITE_API_BASE as string | undefined;
export const API_BASE = (RAW_BASE ?? "").replace(/\/+$/, ""); // sin trailing slash

if (!API_BASE) {
  // fallar rápido si no está configurado en Vercel / .env
  // (evita que la app se "vea rota" sin explicación)
  // En Vercel: Project → Settings → Environment Variables
  //   VITE_API_BASE = https://api.unesumrepo.com
  console.warn(
    "[api] VITE_API_BASE no está definido. Configura la variable de entorno."
  );
}

/** ===== Utilidades ===== */

/** Espera en ms */
function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Combina la señal del caller con un timeout local. */
function withTimeout(
  timeoutMs: number,
  external?: AbortSignal
): AbortSignal {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);

  if (external) {
    // Si AbortSignal.any existe, úsalo; si no, "encadenamos" manualmente
    // @ts-ignore
    const anyFn = (AbortSignal as any).any;
    if (typeof anyFn === "function") {
      // @ts-ignore
      return (AbortSignal as any).any([external, controller.signal]);
    } else {
      if (external.aborted) controller.abort();
      external.addEventListener("abort", () => controller.abort(), {
        once: true,
      });
    }
  }

  // Limpia el timeout cuando se aborte (evita fugas)
  controller.signal.addEventListener("abort", () => clearTimeout(t), {
    once: true,
  });
  return controller.signal;
}

type ReqInit = Omit<RequestInit, "signal"> & {
  signal?: AbortSignal;
  timeoutMs?: number;
};

/** Reintenta en errores transitorios (429/502/503/504) y abort/timeout. */
async function request<T>(
  path: string,
  init: ReqInit = {},
  opts: { retries?: number; backoffMs?: number } = {}
): Promise<T> {
  if (!API_BASE) {
    throw new Error(
      "VITE_API_BASE no configurado. Define VITE_API_BASE en tus variables de entorno."
    );
  }

  const { retries = 2, backoffMs = 500 } = opts;
  const url = `${API_BASE}${path}`;
  let attempt = 0;

  // valores por defecto seguros
  const timeoutMs = init.timeoutMs ?? 15000;
  const headers = {
    Accept: "application/json",
    ...init.headers,
  };

  while (true) {
    try {
      const res = await fetch(url, {
        ...init,
        headers,
        signal: withTimeout(timeoutMs, init.signal),
      });

      // OK → parsea JSON
      if (res.ok) {
        // FastAPI devuelve JSON siempre
        return (await res.json()) as T;
      }

      // Intenta extraer mensaje útil del cuerpo
      let message = `HTTP ${res.status}`;
      try {
        const body = await res.json().catch(() => undefined);
        if (body && typeof body === "object") {
          // FastAPI típicamente: {"detail": "..."}
          if (typeof (body as any).detail === "string") {
            message = (body as any).detail;
          } else if ((body as any).detail) {
            message = JSON.stringify((body as any).detail);
          }
        } else {
          const txt = await res.text().catch(() => "");
          if (txt) message = txt;
        }
      } catch {
        /* ignore */
      }

      // Reintentos para estados transitorios
      if ([429, 502, 503, 504].includes(res.status) && attempt < retries) {
        attempt++;
        await sleep(backoffMs * attempt);
        continue;
      }

      throw new Error(message);
    } catch (err: any) {
      // Abort/timeout o fallo de red: reintenta si quedan intentos
      const isAbort =
        err?.name === "AbortError" ||
        /aborted|abort/i.test(String(err?.message || ""));

      if ((isAbort || err?.name === "TypeError") && attempt < retries) {
        attempt++;
        await sleep(backoffMs * attempt);
        continue;
      }
      // Propaga el error final
      throw err;
    }
  }
}

/** ===== API pública ===== */

export async function search(
  q: string,
  top_k = 10,
  opts?: { signal?: AbortSignal; timeoutMs?: number }
) {
  const top = Math.max(1, Math.min(top_k, 50)); // clamp igual que el backend
  return request<SearchResponse>(
    "/search",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q, top_k: top }),
      signal: opts?.signal,
      timeoutMs: opts?.timeoutMs ?? 15000,
    },
    { retries: 2, backoffMs: 500 }
  );
}

/** Helpers para monitoreo desde UI (opcional) */
export async function healthz() {
  return request<{ ok: boolean }>("/healthz", { timeoutMs: 5000 }, { retries: 0 });
}
export async function ready() {
  return request<{ mapping_ready: boolean }>("/ready", { timeoutMs: 5000 }, { retries: 0 });
}
