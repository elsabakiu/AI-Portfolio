import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";

import { useOnboardingFlow } from "./useOnboardingFlow";

describe("useOnboardingFlow", () => {
  it("reports ready state when profile and watchlist are complete", () => {
    const { result } = renderHook(() =>
      useOnboardingFlow({
        hasDashboardData: false,
        hasWatchlist: true,
        hasProfileSetup: true,
        isStreaming: false,
      })
    );

    expect(result.current.showOnboarding).toBe(true);
    expect(result.current.onboardingReady).toBe(true);
    expect(result.current.readinessLabel).toBe("ready");
  });

  it("reports running state during stream", () => {
    const { result } = renderHook(() =>
      useOnboardingFlow({
        hasDashboardData: false,
        hasWatchlist: true,
        hasProfileSetup: false,
        isStreaming: true,
      })
    );

    expect(result.current.readinessLabel).toBe("running");
  });
});
