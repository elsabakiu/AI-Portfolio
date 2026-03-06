import { Loader2 } from "lucide-react";

export function SectionLoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="rounded-lg border border-border/50 bg-card p-4 text-sm text-muted-foreground">
      <div className="inline-flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>{label}...</span>
      </div>
    </div>
  );
}
