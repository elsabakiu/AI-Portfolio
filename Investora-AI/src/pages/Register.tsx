import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Activity } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useUser } from "@/contexts/UserContext";
import { registerUser } from "@/lib/auth";

const Register = () => {
  const navigate = useNavigate();
  const { login, user, isLoading } = useUser();

  useEffect(() => {
    if (!isLoading && user) {
      navigate("/dashboard", { replace: true });
    }
  }, [isLoading, user, navigate]);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (fullName.trim().length < 3) return setError("Full name must be at least 3 characters");
    if (!email.trim()) return setError("Email address is required");
    if (password.length < 8) return setError("Password must be at least 8 characters");
    if (password !== confirmPassword) return setError("Passwords do not match");

    setLoading(true);
    try {
      const normalizedEmail = email.trim().toLowerCase();
      const result = await registerUser(normalizedEmail, password, {
        displayName: fullName.trim(),
        email: email.trim(),
        riskTolerance: "medium",
        interests: [],
        telegramChatId: "",
      });

      if (!result.ok) {
        setError(result.error || "Registration failed");
        return;
      }

      // Auto-login after registration
      await login(normalizedEmail, password);
      navigate("/dashboard");
    } catch {
      setError("Connection error. Is n8n running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background bg-grid flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-3 justify-center mb-8">
          <div className="w-9 h-9 rounded-lg bg-primary/20 flex items-center justify-center glow-primary">
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <h1 className="text-xl font-mono font-bold text-gradient-primary">Investora AI</h1>
        </div>

        {/* Card */}
        <div className="bg-card border border-border/50 rounded-xl p-6 space-y-5">
          <div>
            <h2 className="text-lg font-mono font-semibold text-foreground">Create Account</h2>
            <p className="text-sm text-muted-foreground font-mono mt-1">
              Set up your investor profile
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                Full Name
              </label>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                className="font-mono bg-background/50"
                required
                autoComplete="name"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="font-mono bg-background/50"
                required
                autoComplete="email"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                  Password
                </label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 8 chars"
                  className="font-mono bg-background/50"
                  required
                  autoComplete="new-password"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                  Confirm
                </label>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat"
                  className="font-mono bg-background/50"
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            {error && <p className="text-xs font-mono text-destructive">{error}</p>}

            <Button type="submit" className="w-full font-mono" disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </Button>

            {/* Terms agreement notice */}
            <p className="text-xs font-mono text-muted-foreground/70 text-center leading-5">
              By creating an account you agree to our{" "}
              <Link to="/terms" className="text-primary hover:underline">Terms of Service</Link>
              {" "}and{" "}
              <Link to="/privacy" className="text-primary hover:underline">Privacy Policy</Link>.
              <br />
              <Link to="/disclaimer" className="text-primary hover:underline">Financial Disclaimer</Link>
              {" "}— AI analysis is not financial advice.
            </p>
          </form>

          <p className="text-center text-sm font-mono text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
