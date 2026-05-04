import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  getSession,
  setSession,
  clearSession,
  loginUser,
  getCurrentUser,
  updateUserProfile,
  type Session,
  type UserProfile,
} from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL as string;

interface UserContextType {
  user: Session | null;
  isLoading: boolean;
  watchlist: string[];
  setWatchlist: (tickers: string[]) => Promise<void>;
  login: (username: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  logout: () => void;
  updateProfile: (profile: UserProfile) => Promise<boolean>;
}

const UserContext = createContext<UserContextType | null>(null);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [watchlist, setWatchlistState] = useState<string[]>([]);
  const navigate = useNavigate();
  const mirroredHashesRef = useRef<Record<string, string>>({});

  const profileHash = (profile: UserProfile): string => {
    try {
      return JSON.stringify(profile);
    } catch {
      return String(Date.now());
    }
  };

  const mirrorProfileToBackend = async (userId: string, profile: UserProfile): Promise<void> => {
    const hash = profileHash(profile);
    const storageKey = `investora_profile_mirror_hash_${userId}`;
    const knownHash = mirroredHashesRef.current[userId] || localStorage.getItem(storageKey) || "";
    if (knownHash === hash) return;

    await fetch(`${API_BASE}/user/${userId}/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    mirroredHashesRef.current[userId] = hash;
    localStorage.setItem(storageKey, hash);
  };

  // Rehydrate session from localStorage on mount (no network call needed)
  useEffect(() => {
    const restoreSession = async () => {
      const session = getSession();
      if (!session) {
        setUser(null);
        setIsLoading(false);
        return;
      }

      // New backend-issued sessions can be validated and refreshed from FastAPI.
      if (session.token) {
        const current = await getCurrentUser(session.token);
        if (current.ok && current.userId && current.username && current.profile) {
          const hydrated: Session = {
            userId: current.userId,
            username: current.username,
            profile: current.profile,
            token: session.token,
          };
          setSession(hydrated);
          setUser(hydrated);
          mirrorProfileToBackend(hydrated.userId, hydrated.profile).catch(() => {
            /* non-critical — silent */
          });
          setIsLoading(false);
          return;
        }

        clearSession();
        setUser(null);
        setIsLoading(false);
        return;
      }

      // Legacy local-only sessions are kept during the migration window so
      // existing users are not forcibly logged out on upgrade.
      setUser(session);
      setIsLoading(false);
      if (session.userId && session.profile) {
        mirrorProfileToBackend(session.userId, session.profile).catch(() => {
          /* non-critical — silent */
        });
      }
    };

    void restoreSession();
  }, []);

  // Load watchlist whenever the logged-in user changes
  useEffect(() => {
    if (!user) {
      setWatchlistState([]);
      return;
    }
    fetch(`${API_BASE}/user/${user.userId}/watchlist`)
      .then((r) => r.json())
      .then((data: unknown) => {
        // Backend returns { user_id, tickers: [] } — extract the array
        const tickers =
          Array.isArray(data)
            ? (data as string[])
            : Array.isArray((data as { tickers?: unknown }).tickers)
            ? ((data as { tickers: string[] }).tickers)
            : [];
        setWatchlistState(tickers);
      })
      .catch(() => {
        /* silently ignore — watchlist is non-critical */
      });
  }, [user?.userId]);

  /** Persist watchlist to backend and update local state */
  const setWatchlist = async (tickers: string[]): Promise<void> => {
    if (!user) return;
    const res = await fetch(`${API_BASE}/user/${user.userId}/watchlist`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers }),
    });
    if (!res.ok) throw new Error(`Watchlist save failed: ${res.status}`);
    setWatchlistState(tickers);
  };

  const login = async (username: string, password: string) => {
    const result = await loginUser(username, password);
    if (result.ok && result.userId && result.profile) {
      const session: Session = {
        username,
        userId: result.userId,
        profile: result.profile,
        token: result.token,
      };
      setSession(session);
      setUser(session);
      mirrorProfileToBackend(session.userId, session.profile).catch(() => {
        /* non-critical — silent */
      });
    }
    return { ok: result.ok, error: result.error };
  };

  const logout = () => {
    clearSession();
    setUser(null);
    setWatchlistState([]);
    navigate("/");
  };

  const updateProfile = async (profile: UserProfile) => {
    if (!user) return false;
    const ok = await updateUserProfile(user.userId, profile);
    if (ok) {
      const updated: Session = { ...user, profile };
      setSession(updated);
      setUser(updated);
      // Keep the mirror cache in sync so the rehydration mirror skips this profile.
      const hash = profileHash(profile);
      mirroredHashesRef.current[user.userId] = hash;
      localStorage.setItem(`investora_profile_mirror_hash_${user.userId}`, hash);
    }
    return ok;
  };

  return (
    <UserContext.Provider
      value={{ user, isLoading, watchlist, setWatchlist, login, logout, updateProfile }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}
