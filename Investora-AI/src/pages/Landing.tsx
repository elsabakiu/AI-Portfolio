import { Link } from "react-router-dom";
import {
  ArrowRight,
  Bell,
  BellRing,
  Bot,
  BrainCircuit,
  Cpu,
  Compass,
  Gauge,
  Layers3,
  Orbit,
  SearchCheck,
  ShieldAlert,
  Radar,
  Target,
  TrendingUp,
  Workflow,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUser } from "@/contexts/UserContext";

const AGENT_STEPS = [
  {
    title: "Data Agent",
    detail: "Scans market, fundamentals, and news streams continuously.",
    icon: Radar,
  },
  {
    title: "Signal Agent",
    detail: "Detects momentum shifts, quality deltas, and anomalies.",
    icon: TrendingUp,
  },
  {
    title: "Personalization Agent",
    detail: "Ranks ideas by your profile, risk, constraints, and watchlist.",
    icon: BrainCircuit,
  },
  {
    title: "Action Agent",
    detail: "Frames the next move: review, monitor, or trim risk.",
    icon: Cpu,
  },
  {
    title: "Delivery Agent",
    detail: "Pushes urgent Telegram alerts and weekly strategic digest.",
    icon: BellRing,
  },
];

const TRUST_CHIPS = [
  "Autonomous multi-agent pipeline",
  "Profile-aware signal ranking",
  "Immediate + weekly delivery",
  "Investor-first action framing",
];

const VALUE_PILLARS = [
  {
    title: "Clarity under pressure",
    detail: "Prioritizes what actually needs your attention now.",
    icon: Target,
  },
  {
    title: "Always-on intelligence",
    detail: "Agents monitor in the background while you stay focused.",
    icon: Orbit,
  },
  {
    title: "Personalized conviction",
    detail: "Matches opportunities to your risk and strategy profile.",
    icon: Gauge,
  },
];

const FEATURE_ITEMS = [
  {
    icon: BrainCircuit,
    title: "Personalized Signal Ranking",
    detail: "Every signal is scored by fit to your risk, interests, constraints, and watchlist context.",
  },
  {
    icon: Bell,
    title: "Real-time Urgency Layer",
    detail: "Critical changes surface instantly through Telegram, while lower urgency stays in dashboard flow.",
  },
  {
    icon: Compass,
    title: "Weekly Strategic Brief",
    detail: "A concise weekly summary with top conviction ideas, key risks, and suggested actions.",
  },
  {
    icon: SearchCheck,
    title: "Discovery Beyond Watchlist",
    detail: "Find relevant opportunities outside your current list without scanning hundreds of tickers manually.",
  },
  {
    icon: ShieldAlert,
    title: "Action Framing",
    detail: "Signals are translated into next-step guidance: review, monitor, or trim risk.",
  },
  {
    icon: Workflow,
    title: "Autonomous Agent Backbone",
    detail: "Data, signal, personalization, and delivery agents run continuously in the background.",
  },
];

export default function Landing() {
  const { user, isLoading } = useUser();

  const primaryHref = !isLoading && user ? "/dashboard" : "/register";
  const primaryLabel = !isLoading && user ? "Open Dashboard" : "Start Free";

  return (
    <div className="min-h-screen bg-background">
      <main>
        <section className="relative overflow-hidden border-b border-border/50">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_10%,rgba(34,211,238,0.2),transparent_40%),radial-gradient(circle_at_88%_12%,rgba(16,185,129,0.16),transparent_36%),linear-gradient(180deg,rgba(7,12,24,0.95)_0%,rgba(5,10,18,1)_100%)]" />
          <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.12)_1px,transparent_1px)] [background-size:36px_36px]" />

          <div className="relative mx-auto grid w-full max-w-6xl gap-10 px-6 pb-16 pt-20 md:items-stretch md:grid-cols-[1.1fr_0.9fr] md:pb-24">
            <div className="space-y-6">
              <p className="inline-flex items-center gap-2 rounded-full border border-primary/35 bg-primary/10 px-3 py-1 text-xs font-mono text-primary">
                <Bot className="h-3.5 w-3.5" />
                AI Copilot for Investor Decisions
              </p>

              <h1 className="text-4xl font-bold leading-tight text-foreground md:text-6xl">
                Autonomous intelligence for what matters in your portfolio.
              </h1>

              <p className="max-w-xl text-base text-slate-300 md:text-lg">
                InvestoraAI runs autonomous agents in the background to detect shifts, rank opportunities by your profile,
                and deliver clear actions through Telegram and weekly strategy updates.
              </p>

              <div className="flex flex-wrap items-center gap-3">
                <Button asChild size="lg" className="gap-2 font-mono">
                  <Link to={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="font-mono">
                  <a href="#intelligence-engine">How the agents work</a>
                </Button>
              </div>

              <div className="flex flex-wrap gap-2 pt-1">
                {TRUST_CHIPS.map((chip) => (
                  <span
                    key={chip}
                    className="rounded border border-slate-700/70 bg-slate-900/55 px-3 py-1.5 text-xs font-mono text-slate-300"
                  >
                    {chip}
                  </span>
                ))}
              </div>
            </div>

            <div className="relative flex">
              <div className="flex h-full w-full min-h-[520px] flex-col rounded-2xl border border-cyan-400/25 bg-slate-950/75 p-4 shadow-[0_0_60px_rgba(34,211,238,0.12)] backdrop-blur-sm">
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-xs font-mono text-cyan-300">Live Intelligence Radar</p>
                  <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[11px] font-mono text-emerald-300">
                    Active
                  </span>
                </div>

                <div className="flex-1 rounded-xl border border-slate-800 bg-gradient-to-b from-slate-950/80 to-slate-900/70 p-4">
                  <svg viewBox="0 0 320 220" className="h-full w-full">
                    <defs>
                      <linearGradient id="lineGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#22d3ee" />
                        <stop offset="100%" stopColor="#10b981" />
                      </linearGradient>
                      <linearGradient id="fillGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.28" />
                        <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.02" />
                      </linearGradient>
                    </defs>
                    <rect x="0" y="0" width="320" height="170" fill="transparent" />
                    <path d="M0 160 L45 150 L90 156 L135 124 L180 132 L225 98 L270 110 L320 70 L320 220 L0 220 Z" fill="url(#fillGlow)" />
                    <path d="M0 160 L45 150 L90 156 L135 124 L180 132 L225 98 L270 110 L320 70" fill="none" stroke="url(#lineGlow)" strokeWidth="3.5" />
                    <circle cx="225" cy="98" r="5" fill="#22d3ee" />
                    <circle cx="320" cy="70" r="5" fill="#10b981" />
                    <line x1="0" y1="188" x2="320" y2="188" stroke="#1e293b" strokeDasharray="3 4" />
                    <line x1="0" y1="132" x2="320" y2="132" stroke="#1e293b" strokeDasharray="3 4" />
                  </svg>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="rounded border border-slate-800 bg-slate-900/80 px-3 py-2 text-slate-300">
                    Highest fit: <span className="text-cyan-300">NVDA</span>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-900/80 px-3 py-2 text-slate-300">
                    Urgent risk: <span className="text-rose-300">TSLA</span>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-900/80 px-3 py-2 text-slate-300">
                    Telegram: <span className="text-emerald-300">enabled</span>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-900/80 px-3 py-2 text-slate-300">
                    Weekly digest: <span className="text-cyan-300">ready</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="relative border-b border-border/50 bg-gradient-to-b from-slate-950/30 via-card/20 to-background">
          <div className="mx-auto w-full max-w-6xl px-6 py-14">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs font-mono text-cyan-300">
                <Layers3 className="h-3.5 w-3.5" />
                Why Investora
              </div>
              <Button asChild size="sm" className="h-8 gap-2 font-mono">
                <Link to={primaryHref}>
                  {primaryLabel}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
            <div className="mb-6 max-w-3xl">
              <h2 className="text-3xl font-semibold text-foreground md:text-4xl">
                Decision confidence, without information overload.
              </h2>
              <p className="mt-3 text-sm text-slate-300 md:text-base">
                Investora turns fragmented market updates into a ranked and personalized decision feed.
                You see what matters now, why it matters, and what to do next.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {VALUE_PILLARS.map((pillar, idx) => (
                <article
                  key={pillar.title}
                  className="rounded-xl border border-slate-800/80 bg-slate-950/55 p-5 shadow-[0_8px_35px_rgba(15,23,42,0.45)]"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <div className="inline-flex rounded-lg border border-cyan-400/30 bg-cyan-500/10 p-2 text-cyan-300">
                      <pillar.icon className="h-4 w-4" />
                    </div>
                    <span className="text-xs font-mono text-slate-500">0{idx + 1}</span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-100">{pillar.title}</h3>
                  <p className="mt-1 text-sm text-slate-400">{pillar.detail}</p>
                </article>
              ))}
            </div>

          </div>
        </section>

        <section id="features" className="border-b border-border/50 bg-card/20">
          <div className="mx-auto w-full max-w-6xl px-6 py-16">
            <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-3xl font-semibold text-foreground">Investora features</h2>
                <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                  A focused feature set built for investor signal quality, speed, and confidence.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button asChild size="sm" className="h-8 gap-2 font-mono">
                  <Link to={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="sm" className="h-8 gap-2 font-mono">
                  <a href="#intelligence-engine">
                    Engine
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {FEATURE_ITEMS.map((item) => (
                <article key={item.title} className="rounded-xl border border-border/70 bg-card/45 p-4">
                  <div className="mb-2 inline-flex rounded-lg border border-primary/30 bg-primary/10 p-2 text-primary">
                    <item.icon className="h-4 w-4" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">{item.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{item.detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="intelligence-engine" className="mx-auto w-full max-w-6xl px-6 py-16">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-3xl font-semibold text-foreground">How Investora thinks</h2>
              <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                A coordinated autonomous agent system transforms raw market noise into prioritized investor actions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-mono text-primary">
                <Workflow className="h-3.5 w-3.5" />
                Agent orchestration
              </span>
              <Button asChild size="sm" className="h-8 gap-2 font-mono">
                <Link to={primaryHref}>
                  {primaryLabel}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-3">
              {AGENT_STEPS.map((step, idx) => (
                <div key={step.title} className="relative rounded-xl border border-border/70 bg-card/45 px-4 py-3">
                  {idx < AGENT_STEPS.length - 1 ? (
                    <span className="absolute left-5 top-[44px] h-6 w-px bg-gradient-to-b from-cyan-400/60 to-transparent" />
                  ) : null}
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-lg bg-primary/15 p-2 text-primary">
                      <step.icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-foreground">
                        {idx + 1}. {step.title}
                      </p>
                      <p className="text-sm text-muted-foreground">{step.detail}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-b from-slate-950/75 to-slate-900/70 p-4">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-700/80 bg-slate-900/70 px-2.5 py-1 text-[11px] font-mono text-slate-300">
                <Radar className="h-3.5 w-3.5 text-cyan-300" />
                Intelligence in motion
              </div>
              <div className="space-y-3">
                <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3">
                  <p className="text-xs font-mono text-slate-400">Detection layer</p>
                  <p className="mt-1 text-sm text-slate-200">Anomalies, trend breaks, and risk shifts across your universe.</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-3">
                  <p className="text-xs font-mono text-slate-400">Decision layer</p>
                  <p className="mt-1 text-sm text-slate-200">Fit scores and action framing aligned to your profile.</p>
                </div>
                <div className="rounded-lg border border-cyan-400/35 bg-cyan-500/10 p-3">
                  <p className="text-xs font-mono text-cyan-200">Delivery layer</p>
                  <p className="mt-1 text-sm text-cyan-100">Immediate Telegram alert for urgency, weekly digest for strategy.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border/50">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 px-6 py-5 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
          <p>For informational purposes only. Not financial advice.</p>
          <div className="inline-flex items-center gap-4">
            <Link to="/terms" className="hover:text-foreground">
              Terms
            </Link>
            <Link to="/privacy" className="hover:text-foreground">
              Privacy
            </Link>
            <Link to="/disclaimer" className="hover:text-foreground">
              Disclaimer
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
