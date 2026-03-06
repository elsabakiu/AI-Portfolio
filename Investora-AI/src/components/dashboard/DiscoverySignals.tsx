import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Info } from "lucide-react";
import type { UserReportBundle } from "@/lib/report";
import { useUser } from "@/contexts/UserContext";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface DiscoverySignalsProps {
  bundle: UserReportBundle | undefined;
  isLoading: boolean;
  isError: boolean;
}

export function DiscoverySignals({ bundle, isLoading, isError }: DiscoverySignalsProps) {
  const { user, watchlist, setWatchlist } = useUser();

  const items = useMemo(() => {
    if (!bundle) return [];
    return [...(bundle.discovery_signals || [])]
      .sort((a, b) => b.fit_score - a.fit_score)
      .slice(0, 6);
  }, [bundle]);

  const potentialCandidates = useMemo(() => {
    if (!bundle) return [];
    const watchlistSet = new Set(watchlist.map((x) => x.toUpperCase()));
    const out: Array<{ ticker: string; signal_type: string; narrative: string }> = [];
    const seen = new Set<string>();
    for (const s of bundle.top_conviction || []) {
      const ticker = s.ticker.toUpperCase();
      if (watchlistSet.has(ticker) || seen.has(ticker)) continue;
      seen.add(ticker);
      out.push({
        ticker,
        signal_type: s.signal_type,
        narrative: s.narrative?.trim() || "Potential candidate from conviction ranking.",
      });
      if (out.length >= 2) break;
    }
    return out;
  }, [bundle, watchlist]);

  const addToWatchlist = async (ticker: string) => {
    const next = Array.from(new Set([...watchlist, ticker.toUpperCase()]));
    await setWatchlist(next);
  };

  if (isLoading) {
    return <div className="rounded-lg border border-border/50 bg-card p-4 text-sm text-muted-foreground">Loading discovery signals...</div>;
  }
  if (isError) {
    return <div className="rounded-lg border border-border/50 bg-card p-4 text-sm text-muted-foreground">Unable to load Discovery Signals</div>;
  }
  if (!bundle) {
    return (
      <div className="rounded-lg border border-border/50 bg-card p-4 text-sm text-muted-foreground">
        Discovery ideas will show once your first analysis is complete.
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-mono text-muted-foreground">Discovery Signals</h3>
          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className="text-muted-foreground/80 hover:text-primary transition-colors"
                  aria-label="About Discovery Signals"
                >
                  <Info className="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs text-xs font-mono leading-relaxed">
                New opportunities outside your watchlist that pass personalization thresholds and are ranked by fit score.
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="rounded-lg border border-border/50 bg-card p-4">
          <p className="text-sm text-foreground">No discovery signals in this run.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            This usually means no outside-watchlist ideas passed your current fit and confidence thresholds.
          </p>

          <p className="mt-3 text-xs font-mono text-muted-foreground">
            Current filters: {user?.profile?.horizon ?? "medium"} horizon • {(user?.profile?.interests || []).length} interests • {(user?.profile?.constraints || []).length} constraints
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              to="/profile"
              className="rounded border border-primary/40 px-2 py-1 text-xs text-primary hover:bg-primary/10"
            >
              Adjust profile filters
            </Link>
            <Link
              to="/watchlist"
              className="rounded border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              Expand watchlist
            </Link>
          </div>

          {potentialCandidates.length > 0 ? (
            <div className="mt-4 space-y-2 border-t border-border/60 pt-3">
              <p className="text-xs font-mono text-muted-foreground">Potential candidates to monitor</p>
              {potentialCandidates.map((c) => {
                const inWatchlist = watchlist.map((x) => x.toUpperCase()).includes(c.ticker);
                return (
                  <div key={c.ticker} className="rounded border border-border/60 bg-background/40 p-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold">{c.ticker}</span>
                        <span className="text-[11px] text-muted-foreground">{c.signal_type}</span>
                      </div>
                      <button
                        type="button"
                        disabled={inWatchlist}
                        onClick={() => addToWatchlist(c.ticker)}
                        className="rounded border border-primary/40 px-2 py-1 text-xs text-primary disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {inWatchlist ? "In Watchlist" : "Add +"}
                      </button>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{c.narrative}</p>
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-mono text-muted-foreground">Discovery Signals</h3>
        <TooltipProvider delayDuration={150}>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="text-muted-foreground/80 hover:text-primary transition-colors"
                aria-label="About Discovery Signals"
              >
                <Info className="h-3.5 w-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent className="max-w-xs text-xs font-mono leading-relaxed">
              New opportunities outside your watchlist that pass personalization thresholds and are ranked by fit score.
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        {items.map((s) => {
          const inWatchlist = watchlist.map((x) => x.toUpperCase()).includes(s.ticker.toUpperCase());
          return (
            <article key={s.signal_id} className="rounded-lg border border-border/50 bg-card p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{s.ticker}</span>
                <span className="text-[11px] text-muted-foreground">{s.signal_type}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{s.narrative?.trim() || "No data available"}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Fit {(s.profile_fit_score * 100).toFixed(0)}% | Confidence {(s.confidence * 100).toFixed(0)}%
              </p>
              <button
                type="button"
                disabled={inWatchlist}
                onClick={() => addToWatchlist(s.ticker)}
                className="mt-2 rounded border border-primary/40 px-2 py-1 text-xs text-primary disabled:cursor-not-allowed disabled:opacity-50"
              >
                {inWatchlist ? "In Watchlist" : "Add to Watchlist +"}
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}
