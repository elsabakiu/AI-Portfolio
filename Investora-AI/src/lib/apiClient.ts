import { z } from "zod";

const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  timeoutMs?: number;
  retries?: number;
}

async function parseErrorPayload(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return await res.text().catch(() => null);
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  const timeoutMs = options.timeoutMs ?? 12_000;
  const retries = options.retries ?? 1;

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    let attempt = 0;
    while (true) {
      try {
        const res = await fetch(`${API_BASE}${path}`, {
          method,
          headers: { "Content-Type": "application/json" },
          body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
          signal: controller.signal,
        });

        if (!res.ok) {
          const details = await parseErrorPayload(res);
          throw new ApiError(`${method} ${path} failed`, res.status, details);
        }

        if (res.status === 204) {
          return undefined as T;
        }

        return (await res.json()) as T;
      } catch (err) {
        const isAbort = err instanceof DOMException && err.name === "AbortError";
        const isRetryable = err instanceof ApiError ? err.status >= 500 : !isAbort;
        if (attempt >= retries || !isRetryable) {
          throw err;
        }
        attempt += 1;
      }
    }
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function apiRequestValidated<T>(
  path: string,
  schema: z.ZodType<T>,
  options: RequestOptions = {}
): Promise<T> {
  const data = await apiRequest<unknown>(path, options);
  const parsed = schema.safeParse(data);
  if (!parsed.success) {
    throw new ApiError(`Schema validation failed for ${path}`, 502, parsed.error.flatten());
  }
  return parsed.data;
}
