import { Button } from "@/components/ui/button";

export function SectionErrorState({
  label,
  onRetry,
}: {
  label: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-lg border border-destructive/40 bg-card p-4 text-sm text-muted-foreground">
      <p className="font-medium text-destructive">{label}</p>
      <p className="mt-1">This section failed to load. Check connectivity or backend health.</p>
      {onRetry ? (
        <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
