import { Link, useLocation } from "react-router-dom";
import { Activity, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useUser } from "@/contexts/UserContext";

export function GlobalHeader() {
  const { user, isLoading, logout } = useUser();
  const location = useLocation();
  const isLoggedIn = Boolean(user);

  const navLinks = [
    { to: "/", label: "Landing" },
    ...(isLoggedIn ? [{ to: "/dashboard", label: "Dashboard" }] : []),
  ];

  return (
    <header className="sticky top-0 z-[60] h-14 border-b border-border/50 bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-full w-full max-w-[1400px] items-center justify-between px-4 md:px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/20 glow-primary">
            <Activity className="h-3.5 w-3.5 text-primary" />
          </div>
          <span className="font-mono text-sm font-bold text-gradient-primary">Investora AI</span>
        </Link>

        <div className="flex items-center gap-2">
          <nav className="hidden items-center gap-1 md:flex">
            {navLinks.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "rounded px-2.5 py-1.5 text-xs font-mono transition-colors",
                  location.pathname === item.to
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          {isLoading ? null : isLoggedIn ? (
            <>
              <Button asChild variant="outline" size="sm" className="h-8 gap-1.5 text-xs font-mono">
                <Link to="/profile">
                  <User className="h-3.5 w-3.5" />
                  <span className="max-w-[110px] truncate">{user?.profile?.displayName || user?.username}</span>
                </Link>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="h-8 gap-1.5 text-xs font-mono text-muted-foreground hover:text-destructive"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm" className="h-8 text-xs font-mono">
                <Link to="/login">Login</Link>
              </Button>
              <Button asChild size="sm" className="h-8 text-xs font-mono">
                <Link to="/register">Get Started</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
