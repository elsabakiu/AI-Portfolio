import { useMemo } from "react";

export function useOnboardingFlow(params: {
  hasDashboardData: boolean;
  hasWatchlist: boolean;
  hasProfileSetup: boolean;
  isStreaming: boolean;
}) {
  const showOnboarding = !params.hasDashboardData;
  const onboardingReady = params.hasWatchlist && params.hasProfileSetup;

  const readinessLabel = useMemo(() => {
    if (params.isStreaming) return "running";
    if (onboardingReady) return "ready";
    return "incomplete";
  }, [onboardingReady, params.isStreaming]);

  return {
    showOnboarding,
    onboardingReady,
    readinessLabel,
  };
}
