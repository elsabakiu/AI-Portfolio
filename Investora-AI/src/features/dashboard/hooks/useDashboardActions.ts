import { useCallback } from "react";
import { toast } from "sonner";

export function useDashboardActions(startStream: (opts?: { skipSynthesis?: boolean; tickers?: string[] }) => Promise<void>) {
  const runAnalysis = useCallback(async () => {
    try {
      await startStream({ skipSynthesis: true });
      toast.success("Analysis run completed");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Run failed";
      toast.error(message);
      throw err;
    }
  }, [startStream]);

  return { runAnalysis };
}
