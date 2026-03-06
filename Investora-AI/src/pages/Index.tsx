import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw, History, CheckCircle2, Circle, ChevronRight, Sparkles, Rocket, Loader2 } from "lucide-react";
import { toast } from "sonner";
import ErrorBoundary from "@/components/ErrorBoundary";
import { MarketStatusBar } from "@/components/MarketStatusBar";
import { StrategyBreakdown } from "@/components/dashboard/StrategyBreakdown";
import { PortfolioPulse } from "@/components/dashboard/PortfolioPulse";
import { ConvictionIdeas } from "@/components/dashboard/ConvictionIdeas";
import { WatchlistAttention } from "@/components/dashboard/WatchlistAttention";
import { DiscoverySignals } from "@/components/dashboard/DiscoverySignals";
import { InvestmentProfileFilters } from "@/components/dashboard/InvestmentProfileFilters";
import { ChatAgent } from "@/components/ChatAgent";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUser } from "@/contexts/UserContext";
import { useDashboard, useLatestReport, useRunHistory, useStreamRun } from "@/lib/report";
import { INTEREST_OPTIONS } from "@/lib/auth";

function SectionFallback({ name }: { name: string }) {
  return (
    <div className="rounded-lg border border-border/50 bg-card p-4 text-sm text-muted-foreground">
      Unable to load {name}
    </div>
  );
}

const Index = () => {
  const { user, watchlist, setWatchlist, updateProfile } = useUser();
  const STARTER_WATCHLIST = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"];
  const INTEREST_LABELS: Record<string, string> = {
    tech: "Tech",
    crypto: "Crypto",
    energy: "Energy",
    forex: "Forex",
    commodities: "Commodities",
  };
  const [showRunHistory, setShowRunHistory] = useState(false);
  const [showProfileSetup, setShowProfileSetup] = useState(false);
  const [setupRisk, setSetupRisk] = useState<"low" | "medium" | "high">("medium");
  const [setupInterests, setSetupInterests] = useState<string[]>([]);
  const [setupTelegram, setSetupTelegram] = useState("");
  const [isSavingSetup, setIsSavingSetup] = useState(false);
  const { data: dashboard, isLoading, isError, error } = useDashboard(user?.userId);
  const { data: latestReport } = useLatestReport();
  const { startStream, isStreaming, nodeProgress } = useStreamRun();
  const { data: runHistory } = useRunHistory();
  const noDashboardYet = isError && (error?.message?.includes("404") ?? false);
  const hasDashboardData = Boolean(dashboard?.run_id);
  const hasWatchlist = watchlist.length > 0;
  const hasProfileSetup = Boolean(
    user?.profile?.riskTolerance &&
      user?.profile?.interests &&
      user.profile.interests.length > 0
  );
  const showOnboarding = noDashboardYet || !hasDashboardData;
  const onboardingReady = hasWatchlist && hasProfileSetup;
  const currentNode = nodeProgress.find((n) => n.status === "running")?.node;
  const currentNodeLabel =
    currentNode
      ?.replaceAll("_", " ")
      .replace(/\b\w/g, (c) => c.toUpperCase()) ?? "Preparing";
  const progressCompleted = nodeProgress.filter((n) => n.status === "completed").length;
  const progressTotal = nodeProgress.length || 1;
  const progressPct = Math.round((progressCompleted / progressTotal) * 100);

  const handleGenerateReport = useCallback(async () => {
    try {
      await startStream({ skipSynthesis: true });
      toast.success("Analysis run completed");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Run failed");
      throw err;
    }
  }, [startStream]);

  const handleSeedStarterWatchlist = useCallback(async () => {
    try {
      await setWatchlist(STARTER_WATCHLIST);
      toast.success("Starter watchlist added");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Could not add starter watchlist");
    }
  }, [setWatchlist]);

  useEffect(() => {
    if (!user?.profile) return;
    setSetupRisk((user.profile.riskTolerance ?? "medium") as "low" | "medium" | "high");
    setSetupInterests([...(user.profile.interests ?? [])]);
    setSetupTelegram(user.profile.telegramChatId ?? "");
  }, [user?.profile]);

  useEffect(() => {
    if (!user || hasDashboardData || !onboardingReady || isStreaming) return;
    const key = `investora-onboarding-autostart-${user.userId}`;
    if (localStorage.getItem(key) === "1") return;
    localStorage.setItem(key, "1");
    handleGenerateReport().catch(() => {
      localStorage.removeItem(key);
    });
  }, [user, hasDashboardData, onboardingReady, isStreaming, handleGenerateReport]);

  const handleApplyDashboardFilters = async (
    updates: {
      horizon: "short" | "medium" | "long";
      interests: string[];
      constraints: string[];
      preferredAssets: string[];
    },
  ) => {
    if (!user) return;
    const current = user.profile;
    const ok = await updateProfile({
      ...current,
      riskTolerance: current.riskTolerance ?? "medium",
      interests: updates.interests,
      telegramChatId: current.telegramChatId ?? "",
      horizon: updates.horizon,
      constraints: updates.constraints,
      preferredAssets: updates.preferredAssets,
    });
    if (!ok) {
      toast.error("Could not save profile filters");
      return;
    }

    toast.success("Profile filters saved. Refreshing personalized dashboard…");
    await handleGenerateReport();
  };

  const toggleSetupInterest = (interest: string) => {
    setSetupInterests((prev) =>
      prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]
    );
  };

  const handleSaveOnboardingProfile = async () => {
    if (!user) return;
    if (setupInterests.length === 0) {
      toast.error("Select at least one interest");
      return;
    }
    setIsSavingSetup(true);
    try {
      const ok = await updateProfile({
        ...user.profile,
        riskTolerance: setupRisk,
        interests: setupInterests,
        telegramChatId: setupTelegram.trim(),
      });
      if (!ok) {
        toast.error("Could not save onboarding profile");
        return;
      }
      toast.success("Profile setup saved");
      setShowProfileSetup(false);
    } finally {
      setIsSavingSetup(false);
    }
  };

  const strategyBreakdown = useMemo(() => {
    const base = latestReport?.strategy_breakdown;
    if (!base) return { quality: [], momentum: [] };
    const topDiscovery = (dashboard?.discovery_signals || []).slice(0, 5).map((x) => x.ticker.toUpperCase());
    const scope = new Set([...watchlist.map((t) => t.toUpperCase()), ...topDiscovery]);
    if (scope.size === 0) return base;
    return {
      quality: base.quality.filter((i) => scope.has(i.company.toUpperCase())),
      momentum: base.momentum.filter((i) => scope.has(i.company.toUpperCase())),
    };
  }, [latestReport, dashboard, watchlist]);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <MarketStatusBar />

      <header className="sticky top-0 z-30 border-b border-border/50 bg-background/90 px-6 py-4 backdrop-blur-sm">
        <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-bold text-foreground">Dashboard</h1>
            <p className="text-xs text-muted-foreground">Personalized signals and portfolio context</p>
          </div>
          <div className="flex items-center gap-2">
            <InvestmentProfileFilters
              profile={user?.profile}
              isApplying={isStreaming}
              onApply={handleApplyDashboardFilters}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateReport}
              disabled={isStreaming}
              className="h-8 gap-1.5 text-xs font-mono"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isStreaming ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">{isStreaming ? "Running…" : "Run Analysis"}</span>
            </Button>
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRunHistory((v) => !v)}
                className="h-8 gap-1.5 text-xs font-mono"
              >
                <History className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">History</span>
              </Button>
              {showRunHistory && runHistory && runHistory.length > 0 && (
                <div className="absolute right-0 top-full z-50 mt-1 w-72 space-y-0.5 rounded-lg border border-border bg-card p-2 shadow-xl">
                  {runHistory.slice(0, 5).map((run) => (
                    <div key={run.run_id} className="flex items-center justify-between rounded px-3 py-2 text-xs font-mono hover:bg-muted">
                      <span>{run.run_date}</span>
                      <span className="text-muted-foreground">{run.signal_count} sig</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-[1400px] flex-1 space-y-5 px-6 py-5">
        {showOnboarding ? (
          <section className="rounded-xl border border-primary/30 bg-gradient-to-br from-primary/10 via-primary/5 to-background p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] font-mono text-primary">
                  <Sparkles className="h-3.5 w-3.5" />
                  First-time setup
                </p>
                <h2 className="mt-2 text-lg font-semibold text-foreground">Your dashboard is getting ready</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Everything is working. Complete the quick setup below and Investora will generate your first personalized insights.
                </p>
              </div>
              <Button
                size="sm"
                onClick={handleGenerateReport}
                disabled={isStreaming || !onboardingReady}
                className="h-8 gap-1.5 text-xs font-mono"
              >
                {isStreaming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Rocket className="h-3.5 w-3.5" />}
                {isStreaming ? "Generating Insights…" : "Run First Analysis"}
              </Button>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-border/60 bg-background/50 p-3">
                <p className="text-xs font-mono text-muted-foreground">Step 1</p>
                <div className="mt-1 flex items-center justify-between">
                  <p className="text-sm text-foreground">Starter watchlist</p>
                  {hasWatchlist ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
                </div>
                {!hasWatchlist ? (
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={handleSeedStarterWatchlist}
                      className="inline-flex items-center gap-1 rounded border border-primary/40 px-2 py-1 text-xs text-primary hover:bg-primary/10"
                    >
                      Add starter tickers
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                    <Link to="/watchlist" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary">
                      Or set manually
                      <ChevronRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                ) : (
                  <p className="mt-1 text-xs text-emerald-300">Ready</p>
                )}
              </div>
              <div className="rounded-lg border border-border/60 bg-background/50 p-3">
                <p className="text-xs font-mono text-muted-foreground">Step 2</p>
                <div className="mt-1 flex items-center justify-between">
                  <p className="text-sm text-foreground">Investment profile</p>
                  {hasProfileSetup ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
                </div>
                {!hasProfileSetup ? (
                  <button
                    type="button"
                    onClick={() => setShowProfileSetup((v) => !v)}
                    className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    {showProfileSetup ? "Hide setup" : "Complete setup"}
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                ) : (
                  <p className="mt-1 text-xs text-emerald-300">Ready</p>
                )}
              </div>
              <div className="rounded-lg border border-border/60 bg-background/50 p-3">
                <p className="text-xs font-mono text-muted-foreground">Step 3</p>
                <div className="mt-1 flex items-center justify-between">
                  <p className="text-sm text-foreground">First analysis run</p>
                  {hasDashboardData ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <Circle className="h-4 w-4 text-muted-foreground" />}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {isStreaming ? "Generating now..." : onboardingReady ? "Ready to run" : "Complete steps 1 and 2"}
                </p>
              </div>
            </div>

            {!hasProfileSetup && showProfileSetup ? (
              <div className="mt-4 rounded-lg border border-border/60 bg-card/40 p-4">
                <p className="text-xs font-mono text-primary">Step 2 setup</p>
                <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-mono text-muted-foreground">Risk profile</label>
                    <Select value={setupRisk} onValueChange={(v) => setSetupRisk(v as "low" | "medium" | "high")}>
                      <SelectTrigger className="h-8 font-mono text-xs bg-background/60">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5 lg:col-span-2">
                    <label className="text-xs font-mono text-muted-foreground">Telegram chat ID (optional)</label>
                    <Input
                      value={setupTelegram}
                      onChange={(e) => setSetupTelegram(e.target.value)}
                      placeholder="e.g. 123456789"
                      className="h-8 bg-background/60 font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="mt-3 space-y-1.5">
                  <label className="text-xs font-mono text-muted-foreground">Interests</label>
                  <div className="flex flex-wrap gap-2">
                    {INTEREST_OPTIONS.map((opt) => (
                      <Badge
                        key={opt}
                        variant="outline"
                        className={`cursor-pointer font-mono text-xs transition-all select-none ${
                          setupInterests.includes(opt)
                            ? "bg-primary/15 text-primary border-primary/40"
                            : "text-muted-foreground hover:text-foreground hover:border-border"
                        }`}
                        onClick={() => toggleSetupInterest(opt)}
                      >
                        {INTEREST_LABELS[opt] ?? opt}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="mt-3">
                  <Button
                    size="sm"
                    onClick={handleSaveOnboardingProfile}
                    disabled={isSavingSetup}
                    className="h-8 text-xs font-mono"
                  >
                    {isSavingSetup ? "Saving..." : "Save step 2 setup"}
                  </Button>
                </div>
              </div>
            ) : null}

            {isStreaming ? (
              <div className="mt-4 rounded-lg border border-cyan-400/35 bg-cyan-500/10 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-mono text-cyan-200">Building your first personalized dashboard</p>
                  <p className="text-xs font-mono text-cyan-300">{progressPct}%</p>
                </div>
                <p className="mt-1 text-sm text-cyan-100">Current stage: {currentNodeLabel}</p>
                <div className="mt-2 h-1.5 rounded bg-cyan-950/50">
                  <div className="h-1.5 rounded bg-cyan-400 transition-all" style={{ width: `${Math.max(6, progressPct)}%` }} />
                </div>
              </div>
            ) : null}

            <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div className="rounded-lg border border-border/60 bg-card/40 p-3">
                <p className="text-xs font-mono text-primary">What you will get</p>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  <li>Top conviction ideas ranked for your profile</li>
                  <li>Watchlist signals prioritized by urgency</li>
                  <li>Discovery opportunities beyond your watchlist</li>
                </ul>
              </div>
              <div className="rounded-lg border border-border/60 bg-card/40 p-3">
                <p className="text-xs font-mono text-primary">After first run</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  The full dashboard sections will populate automatically and continue refreshing as you run new analyses.
                </p>
              </div>
            </div>
          </section>
        ) : null}

        {showOnboarding ? (
          <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {[
              {
                title: "Portfolio Pulse",
                text: "Daily watchlist move, market regime, and risk alignment will appear here.",
              },
              {
                title: "Highest-Conviction Ideas",
                text: "Your top 3 personalized opportunities will be ranked after the first run.",
              },
              {
                title: "Watchlist Attention",
                text: "Priority watchlist signals with urgency and suggested action will show here.",
              },
              {
                title: "Discovery Signals",
                text: "New opportunities outside your watchlist will appear when profile fit is high enough.",
              },
            ].map((item) => (
              <article key={item.title} className="rounded-lg border border-border/50 bg-card/40 p-4">
                <p className="text-sm font-mono text-muted-foreground">{item.title}</p>
                <p className="mt-2 text-sm text-muted-foreground">{item.text}</p>
              </article>
            ))}
          </section>
        ) : (
          <>
            <ErrorBoundary fallback={<SectionFallback name="Portfolio Pulse" />}>
              <PortfolioPulse
                bundle={dashboard}
                watchlist={watchlist}
                isLoading={isLoading}
                isError={isError && !noDashboardYet}
              />
            </ErrorBoundary>

            <ErrorBoundary fallback={<SectionFallback name="Highest-Conviction Ideas" />}>
              <ConvictionIdeas
                bundle={dashboard}
                isLoading={isLoading}
                isError={isError && !noDashboardYet}
              />
            </ErrorBoundary>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <ErrorBoundary fallback={<SectionFallback name="Watchlist Attention" />}>
                <WatchlistAttention
                  bundle={dashboard}
                  isLoading={isLoading}
                  isError={isError && !noDashboardYet}
                />
              </ErrorBoundary>
              <ErrorBoundary fallback={<SectionFallback name="Discovery Signals" />}>
                <DiscoverySignals
                  bundle={dashboard}
                  isLoading={isLoading}
                  isError={isError && !noDashboardYet}
                />
              </ErrorBoundary>
            </div>

            <ErrorBoundary fallback={<SectionFallback name="Strategy Breakdown" />}>
              <StrategyBreakdown breakdown={strategyBreakdown} />
            </ErrorBoundary>
          </>
        )}

      </div>

      <footer className="mt-4 border-t border-border/50 pb-16">
        <div className="mx-auto flex max-w-[1400px] flex-col items-center justify-between gap-3 px-6 py-4 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} InvestoraAI — For informational purposes only. Not financial advice.
          </p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link to="/terms" className="transition-colors hover:text-primary">Terms of Service</Link>
            <Link to="/privacy" className="transition-colors hover:text-primary">Privacy Policy</Link>
            <Link to="/disclaimer" className="transition-colors hover:text-primary">Financial Disclaimer</Link>
          </div>
        </div>
      </footer>
      <ChatAgent />
    </div>
  );
};

export default Index;
