// InvestoraAI auth helpers
// FastAPI is the source of truth for auth.
// Only { username, userId, profile } is cached in localStorage for session rehydration.

/** A manually entered portfolio position (v3). No cost basis in MVP. */
export interface Position {
  ticker: string;
  shares: number;
}

export interface UserProfile {
  // ── Existing fields ───────────────────────────────────────
  riskTolerance: "low" | "medium" | "high";
  interests: string[];
  telegramChatId: string;
  // ── New v2 fields (optional for backward-compat with old sessions) ──
  displayName?: string;
  email?: string;
  riskTolerancePercent?: number;   // 0-100 slider value
  defaultMarket?: "US" | "EU";
  baseCurrency?: "USD" | "EUR" | "GBP";
  dailyEmailDigest?: boolean;
  weeklyEmailDigest?: boolean;
  alertNotifications?: boolean;
  // ── New v3 fields ─────────────────────────────────────────
  horizon?: "short" | "medium" | "long";   // investment time horizon
  constraints?: string[];                   // e.g. ["no_crypto", "ESG", "max_20pct"]
  preferredAssets?: string[];               // e.g. ["stocks", "ETFs", "crypto"]
  positions?: Position[];                   // manually entered portfolio positions
}

export interface Session {
  username: string;
  userId: string;
  profile: UserProfile;
  token?: string;
}

export const INTEREST_OPTIONS = ["tech", "crypto", "energy", "forex", "commodities"] as const;
export const RISK_OPTIONS = ["low", "medium", "high"] as const;
export const MARKET_OPTIONS = ["US", "EU"] as const;
export const CURRENCY_OPTIONS = ["USD", "EUR", "GBP"] as const;
// v3 options
export const HORIZON_OPTIONS = ["short", "medium", "long"] as const;
export const CONSTRAINT_OPTIONS = ["no_crypto", "ESG", "max_20pct"] as const;
export const ASSET_OPTIONS = ["stocks", "ETFs", "crypto"] as const;

const API_BASE = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");
const SESSION_KEY = "investora_session";
// --- Backend API calls ---

export async function registerUser(
  username: string,
  password: string,
  profile: UserProfile
): Promise<{ ok: boolean; error?: string; userId?: string; token?: string }> {
  const userId = crypto.randomUUID();

  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, userId, profile }),
  });

  return res.json() as Promise<{ ok: boolean; error?: string; userId?: string; token?: string }>;
}

export async function loginUser(
  username: string,
  password: string
): Promise<{ ok: boolean; userId?: string; profile?: UserProfile; token?: string; error?: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  return res.json() as Promise<{ ok: boolean; userId?: string; profile?: UserProfile; token?: string; error?: string }>;
}

export async function getCurrentUser(
  token: string
): Promise<{ ok: boolean; userId?: string; username?: string; profile?: UserProfile; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      return { ok: false, error: `Request failed with ${res.status}` };
    }
    const data = (await res.json()) as {
      ok?: boolean;
      userId?: string;
      username?: string;
      profile?: UserProfile;
    };
    return {
      ok: data.ok === true,
      userId: data.userId,
      username: data.username,
      profile: data.profile,
    };
  } catch {
    return { ok: false, error: "Connection error" };
  }
}

export async function updateUserProfile(
  userId: string,
  profile: UserProfile
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/user/${userId}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { ok?: boolean };
    return data.ok === true;
  } catch {
    return false;
  }
}

// --- localStorage session helpers ---

export function getSession(): Session | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function setSession(data: Session): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(data));
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
}
